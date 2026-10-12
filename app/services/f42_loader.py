# ruff: noqa: BLE001  – broad except blocks are intentional diagnostic catches
"""F42 OPTA feed loader - loads data into the database."""

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session, aliased

from app.constants import DraftPositionConstants, RealMatchPeriod
from app.models import (
    RealCompetition,
    RealMatch,
    RealMatchTeam,
    RealPlayer,
    RealTeam,
)
from app.services.f42_parser import F42Parser
from app.services.save_mds import SaveMDS
from app.services.sync_fantasy import SyncFantasyService
from app.services.sync_real import SyncRealService
from app.utils.dt import utc_now
from app.utils.processes import Process, Task
from app.utils.scalars import to_float, to_int


class F42Loader:
    """Load F42 parsed data into the database."""

    @staticmethod
    def load_file(db: Session, process: Process, tmp_name: str | None = None) -> Process:
        """Parse and load an F42 file into the database.

        Args:
            db: Database session
            process: Process row (already created by log_feed_start)
            tmp_name: Path to the temporary file containing the F42 data

        Returns:
            Process row stamped with processing results.
        """
        from app.services.f_loader import FLoader  # lazy — avoids circular import

        file_path = tmp_name or process.process_name
        task = process.create_task(
            name=f"Load {F42Parser._FEED} file: {file_path}",
            status=Task.RUNNING,
            status_on_error=Task.ERROR,
        )
        task.init_info(
            "realCompetitionID", "realCompetitionSYMID", "realCompetitionSeasonId"
        )
        try:
            parsed_data = F42Parser.parse_file(process, file_path)
            task.assign(
                "realCompetitionSYMID",
                parsed_data["competition"].get("realCompetitionSYMID"),
            )
            task.assign(
                "realCompetitionSeasonId",
                parsed_data["competition"].get("realCompetitionSeasonId"),
            )
        except Exception as e:
            task.add_error(f"Error parsing feed [{type(e).__name__}]: {e!s}")
            task.close(status=Task.ERROR)
            return FLoader.log_feed_end(db, process)

        # Load competitions
        try:
            _, comp_data = F42Loader._load_competition(
                db, process, parsed_data["competition"]
            )
            if "realCompetitionID" not in comp_data:
                task.add_error("Competition not found — feed skipped")
                task.close(status=Task.ERROR)
                return FLoader.log_feed_end(db, process)
            task.assign("realCompetitionID", comp_data["realCompetitionID"])
        except Exception as e:
            db.rollback()
            task.add_error(f"Error loading competition [{type(e).__name__}]: {e!s}")
            task.close(status=Task.ERROR)
            return FLoader.log_feed_end(db, process)

        # Load teams
        team_id_mapping = {}
        try:
            _, team_id_mapping = F42Loader._load_teams(
                db, process, parsed_data["teams"], comp_data
            )
        except Exception as e:
            db.rollback()
            task.add_error(f"Error loading teams [{type(e).__name__}]: {e!s}")
            task.close(status=Task.ERROR)
            return FLoader.log_feed_end(db, process)

        # Load players
        try:
            F42Loader._load_players(
                db, process, parsed_data["players"], comp_data, team_id_mapping
            )
        except Exception as e:
            db.rollback()
            task.add_error(f"Error loading players [{type(e).__name__}]: {e!s}")
            task.close(status=Task.ERROR)
            return FLoader.log_feed_end(db, process)

        # Pre-load existing matches cache
        matches_cache = {}
        try:
            matches_cache = F42Loader._load_matches_cache(db, comp_data)
        except Exception as e:
            db.rollback()
            task.add_error(f"Error pre-loading matches [{type(e).__name__}]: {e!s}")
            task.close(status=Task.ERROR)
            return FLoader.log_feed_end(db, process)

        # Build teams cache from loaded teams
        teams_cache = {}
        try:
            for team_data in parsed_data["teams"]:
                team_uid = team_data.get("realTeamUID")
                if team_uid in team_id_mapping:
                    team_result = db.execute(
                        select(RealTeam.realTeamID, RealTeam.realTeamName, RealTeam.realTeamShortName)
                        .where(
                            RealTeam.realCompetitionID == comp_data["realCompetitionID"],
                            RealTeam.realTeamUID == team_uid,
                        )
                        .limit(1)
                    ).first()
                    if team_result:
                        teams_cache[team_uid] = list(team_result)
        except Exception as e:
            db.rollback()
            task.add_error(f"Error building teams cache [{type(e).__name__}]: {e!s}")
            task.close(status=Task.ERROR)
            return FLoader.log_feed_end(db, process)

        # Load matches
        try:
            F42Loader._load_matches(
                db,
                process,
                parsed_data["matches"],
                matches_cache,
                teams_cache,
                comp_data,
            )
        except Exception as e:
            db.rollback()
            task.add_error(f"Error loading matches [{type(e).__name__}]: {e!s}")

        try:
            F42Loader._save_mds(db, process, comp_data["realCompetitionID"])
        except Exception as e:
            db.rollback()
            task.add_error(f"Error saving MDS data [{type(e).__name__}]: {e!s}")

        try:
            F42Loader._sync(db, process, comp_data["realCompetitionID"], include_rtm=True)
        except Exception as e:
            db.rollback()
            task.add_error(f"Error syncing data [{type(e).__name__}]: {e!s}")

        task.close(status=Task.COMPLETED if not task.errors else Task.ERROR)
        return FLoader.log_feed_end(db, process)

    @staticmethod
    def _sync(db: Session, f42_process: Process, real_competition_id: int, include_rtm: bool = False) -> None:
        # sync_real and sync_fantasy each get their own Process record linked back to the f42 feed
        try:
            SyncRealService.sync_all(db, real_competition_id, include_rtm=include_rtm, prev_process=f42_process)
            db.commit()
        except Exception:
            db.rollback()

        try:
            SyncFantasyService.sync_all(db, real_competition_id, prev_process=f42_process)
            db.commit()
        except Exception:
            db.rollback()

    @staticmethod
    def _save_mds(db: Session, f42_process: Process, real_competition_id: int) -> None:
        mds_process = Process.init_save_mds_process(
            db, str(real_competition_id), prevProcess=f42_process
        )
        SaveMDS(db, real_competition_id, mds_process).process()
        db.commit()

    @staticmethod
    def _load_competition(
        db: Session, process: Process, comp_data: dict
    ) -> tuple[Task, dict[str, str | int | datetime | None]]:
        """Look up a competition in RealCompetitions and stamp lastF42Date.

        Competitions are managed externally — this loader does not insert.
        """
        task = process.create_task(
            name="Load Competition", status=Task.RUNNING, status_on_error=Task.ERROR
        )
        task.init_info("updated")
        # Query for existing competition
        row = (
            db.execute(
                select(
                    RealCompetition.realCompetitionID,
                    RealCompetition.baseRealCompetitionID,
                    RealCompetition.extraRealCompetitionID,
                    RealCompetition.realCompetitionUID,
                    RealCompetition.realCompetitionCountry,
                    RealCompetition.realCompetitionFirstMatchDay,
                    RealCompetition.realCompetitionLastMatchDay,
                )
                .where(
                    RealCompetition.realCompetitionSYMID == comp_data["realCompetitionSYMID"],
                    RealCompetition.realCompetitionSeasonId == comp_data["realCompetitionSeasonId"],
                )
                .limit(1)
            )
            .mappings()
            .first()
        )

        if row:
            db.execute(
                update(RealCompetition)
                .where(RealCompetition.realCompetitionID == row["realCompetitionID"])
                .values(
                    lastF42Date=comp_data["lastF42Date"],
                    updatedIn=utc_now(),
                )
            )
            task.inc("updated")
            comp_data = dict(row) | comp_data
        task.close(status=Task.COMPLETED if not task.errors else Task.ERROR)
        return (
            task,
            comp_data,
        )  # No competition found; return input data for error handling

    @staticmethod
    def _load_teams(
        db: Session, process: Process, teams_data: list, comp_data: dict[str, str | int | datetime | None]
    ) -> tuple[Task, dict[str, int]]:
        """Load or update teams in RealTeams.

        Returns:
            Dictionary with inserted, updated counts and team_uid_mapping
        """
        task = process.create_task(name="Load Teams", status=Task.RUNNING, status_on_error=Task.ERROR)
        task.init_info("inserted", "updated")
        team_uid_mapping = {}  # Map team uID to realTeamID for later use

        for team_data in teams_data:
            if not (team_data.get("realTeamUID") and team_data.get("realTeamName")):
                continue

            # Query for existing team
            result = db.scalars(
                select(RealTeam.realTeamID)
                .where(
                    RealTeam.realCompetitionID == comp_data["realCompetitionID"],
                    RealTeam.realTeamUID == team_data["realTeamUID"],
                )
                .limit(1)
            ).first()

            if result:
                # Update existing
                db.execute(
                    update(RealTeam)
                    .where(RealTeam.realTeamID == result)
                    .values(
                        realTeamName=team_data["realTeamName"],
                        realTeamSYMID=team_data["realTeamSYMID"],
                        realTeamShortName=team_data["realTeamSYMID"],
                        lastF42Date=comp_data["lastF42Date"],
                        lastFDate=comp_data["lastF42Date"],
                        updatedIn=task.start_time,
                    )
                )
                task.inc("updated")
            else:
                # Insert new
                new_team = RealTeam(
                    realCompetitionID=comp_data["realCompetitionID"],
                    realCompetitionUID=comp_data["realCompetitionUID"],
                    realCompetitionSYMID=comp_data["realCompetitionSYMID"],
                    realCompetitionSeasonId=comp_data["realCompetitionSeasonId"],
                    baseRealCompetitionID=comp_data["baseRealCompetitionID"],
                    extraRealCompetitionID=comp_data["extraRealCompetitionID"],
                    realTeamUID=team_data["realTeamUID"],
                    realTeamName=team_data["realTeamName"],
                    realTeamSYMID=team_data["realTeamSYMID"],
                    realTeamShortName=team_data["realTeamSYMID"],
                    realTeamCountry=comp_data["realCompetitionCountry"],
                    position=DraftPositionConstants.EPL_TEAM,
                    draftPosition=DraftPositionConstants.EPL_TEAM,
                    draftPositionOrder=DraftPositionConstants.get_order(
                        DraftPositionConstants.EPL_TEAM
                    ),
                    isProcessedMember=0,
                    lastF42Date=comp_data["lastF42Date"],
                    lastFDate=comp_data["lastF42Date"],
                    createdIn=task.start_time,
                    updatedIn=task.start_time,
                )
                db.add(new_team)
                db.flush()
                team_uid_mapping[team_data["realTeamUID"]] = new_team.realTeamID
                task.inc("inserted")

            # Also store existing team IDs in mapping
            if result and team_data["realTeamUID"] not in team_uid_mapping:
                team_uid_mapping[team_data["realTeamUID"]] = result

        task.close(status=Task.COMPLETED if not task.errors else Task.ERROR)
        return (task, team_uid_mapping)

    @staticmethod
    def _load_players(
        db: Session,
        process: Process,
        players_data: list,
        comp_data: dict,
        team_uid_mapping: dict,
    ) -> Task:
        """Load or update players in RealPlayers."""
        task = process.create_task(
            name="Load Players", status=Task.RUNNING, status_on_error=Task.ERROR
        )
        task.init_info("inserted", "updated")

        def safe_date(value):
            if not value or value.lower() == "unknown":
                return None
            try:
                datetime.strptime(value, "%Y-%m-%d")  # noqa: DTZ007 — validates format only, result discarded
                return value
            except (ValueError, TypeError):
                return None

        for player_data in players_data:
            if not (
                player_data.get("realPlayerUID") and player_data.get("realTeamUID")
            ):
                continue

            # Get realTeamID from mapping
            real_team_id = team_uid_mapping.get(player_data["realTeamUID"])
            if not real_team_id:
                continue

            # Check for existing player
            result = db.scalars(
                select(RealPlayer.realPlayerID)
                .where(
                    RealPlayer.realCompetitionID == comp_data["realCompetitionID"],
                    RealPlayer.realPlayerUID == player_data["realPlayerUID"],
                )
                .limit(1)
            ).first()

            # Calculate draft position
            draft_position_order = DraftPositionConstants.get_order(
                player_data.get("position"), player_data.get("realPosition")
            )
            draft_position = (
                DraftPositionConstants.get_position(draft_position_order)
                if draft_position_order
                else None
            )

            if result:
                # Update existing
                db.execute(
                    update(RealPlayer)
                    .where(RealPlayer.realPlayerID == result)
                    .values(
                        firstName=player_data.get("firstName"),
                        lastName=player_data.get("lastName"),
                        knownName=player_data.get("knownName"),
                        position=player_data.get("position"),
                        realPosition=player_data.get("realPosition"),
                        birthDate=safe_date(player_data.get("birthDate")),
                        weight=to_float(player_data.get("weight")),
                        height=to_float(player_data.get("height")),
                        jerseyNumber=to_int(player_data.get("jerseyNumber")),
                        draftPosition=draft_position,
                        draftPositionOrder=draft_position_order,
                        lastF42Date=comp_data["lastF42Date"],
                        lastFDate=comp_data["lastF42Date"],
                        updatedIn=task.start_time,
                    )
                )
                task.inc("updated")
            else:
                # Insert new
                db.add(
                    RealPlayer(
                        realCompetitionID=comp_data["realCompetitionID"],
                        realCompetitionUID=comp_data["realCompetitionUID"],
                        realCompetitionSYMID=comp_data["realCompetitionSYMID"],
                        realCompetitionSeasonId=comp_data["realCompetitionSeasonId"],
                        baseRealCompetitionID=comp_data["baseRealCompetitionID"],
                        extraRealCompetitionID=comp_data["extraRealCompetitionID"],
                        realTeamID=real_team_id,
                        realTeamUID=player_data["realTeamUID"],
                        realPlayerUID=player_data["realPlayerUID"],
                        firstName=player_data.get("firstName"),
                        lastName=player_data.get("lastName"),
                        knownName=player_data.get("knownName"),
                        position=player_data.get("position"),
                        realPosition=player_data.get("realPosition"),
                        birthDate=safe_date(player_data.get("birthDate")),
                        weight=to_float(player_data.get("weight")),
                        height=to_float(player_data.get("height")),
                        jerseyNumber=to_int(player_data.get("jerseyNumber")),
                        draftPosition=draft_position,
                        draftPositionOrder=draft_position_order,
                        isProcessedMember=0,
                        lastF42Date=comp_data["lastF42Date"],
                        lastFDate=comp_data["lastF42Date"],
                        createdIn=task.start_time,
                        updatedIn=task.start_time,
                    )
                )
                task.inc("inserted")

        task.close(status=Task.COMPLETED if not task.errors else Task.ERROR)
        return task

    @staticmethod
    def _load_matches_cache(db: Session, comp_data: dict) -> dict:
        """Pre-load existing RealMatches and RealMatchTeams IDs into a cache.

        Returns:
            Dictionary with key="tUID_1,tUID_2" → [realMatchID, mtID_1, mtID_2]
        """
        cache = {}

        t1 = aliased(RealMatchTeam)
        t2 = aliased(RealMatchTeam)
        results = (
            db.execute(
                select(
                    RealMatch.realMatchID.label("mID"),
                    t1.realMatchTeamID.label("mtID_1"),
                    t2.realMatchTeamID.label("mtID_2"),
                    t1.realTeamUID.label("tUID_1"),
                    t2.realTeamUID.label("tUID_2"),
                )
                .join(t1, (t1.realMatchID == RealMatch.realMatchID) & (t1.realTeamNumber == 1))
                .join(t2, (t2.realMatchID == RealMatch.realMatchID) & (t2.realTeamNumber == 2))
                .where(RealMatch.realCompetitionID == comp_data["realCompetitionID"])
            )
            .mappings()
            .all()
        )

        for row in results:
            key = f"{row['tUID_1']},{row['tUID_2']}"
            cache[key] = [row["mID"], row["mtID_1"], row["mtID_2"]]

        return cache

    @staticmethod
    def _load_matches(
        db: Session,
        process: Process,
        matches_data: list,
        matches_cache: dict,
        teams_cache: dict,
        comp_data: dict,
    ) -> Task:
        """Load or update matches and match teams."""
        task = process.create_task(
            name="Load Matches", status=Task.RUNNING, status_on_error=Task.ERROR
        )
        task.init_info("inserted", "updated")

        for match_data in matches_data:
            if not match_data.get("team_data") or len(match_data["team_data"]) < 2:
                continue

            # Get the two teams (Home and Away)
            home_team_data = next(
                (t for t in match_data["team_data"] if t["side"] == "Home"), None
            )
            away_team_data = next(
                (t for t in match_data["team_data"] if t["side"] == "Away"), None
            )

            if not (home_team_data and away_team_data):
                continue

            home_team_uid = home_team_data.get("team_ref")
            away_team_uid = away_team_data.get("team_ref")

            if not (home_team_uid and away_team_uid):
                continue

            # Build the key for cache lookup
            cache_key = f"{home_team_uid},{away_team_uid}"

            # Get team info from teams cache
            home_team_info = teams_cache.get(home_team_uid)
            away_team_info = teams_cache.get(away_team_uid)

            if not (home_team_info and away_team_info):
                continue

            # Check if match exists in cache
            if cache_key in matches_cache:
                # Update existing match
                real_match_id, *_ = matches_cache[cache_key]
                db.execute(
                    update(RealMatch)
                    .where(RealMatch.realMatchID == real_match_id)
                    .values(
                        realMatchType=match_data.get("match_type"),
                        realMatchPeriod=match_data.get("period"),
                        realMatchRealPeriod=match_data.get("period"),
                        realMatchDate=match_data.get("date_utc"),
                        realCompetitionMatchDay=match_data.get("match_day"),
                        lastF42Date=task.start_time,
                        updatedIn=task.start_time,
                    )
                )
                task.inc("updated")
            else:
                # Insert new match
                new_match = RealMatch(
                    realCompetitionID=comp_data["realCompetitionID"],
                    realCompetitionUID=comp_data["realCompetitionUID"],
                    realCompetitionSYMID=comp_data["realCompetitionSYMID"],
                    realCompetitionSeasonId=comp_data["realCompetitionSeasonId"],
                    realCompetitionMatchDay=match_data.get("match_day"),
                    realCompetitionFirstMatchDay=comp_data[
                        "realCompetitionFirstMatchDay"
                    ],
                    realCompetitionLastMatchDay=comp_data[
                        "realCompetitionLastMatchDay"
                    ],
                    baseRealCompetitionID=comp_data["baseRealCompetitionID"],
                    extraRealCompetitionID=comp_data["extraRealCompetitionID"],
                    realMatchType=match_data.get("match_type"),
                    realMatchStatus=RealMatchPeriod.to_match_status(
                        match_data.get("period")
                    ),
                    realMatchPeriod=match_data.get("period"),
                    realMatchRealPeriod=match_data.get("period"),
                    realMatchDate=match_data.get("date_utc"),
                    realMatchDateOffset=match_data.get("date_offset"),
                    realMatchEnded=RealMatchPeriod.to_match_ended(
                        match_data.get("period")
                    ),
                    realMatchIgnore=0,
                    enabled=1,
                    lastF42Date=task.start_time,
                    createdIn=task.start_time,
                    updatedIn=task.start_time,
                )
                db.add(new_match)
                db.flush()
                real_match_id = new_match.realMatchID
                task.inc("inserted")

                # Insert RealMatchTeams for Home and Away
                for side, team_uid, team_id, team_info in [
                    ("Home", home_team_uid, home_team_info[0], home_team_info),
                    ("Away", away_team_uid, away_team_info[0], away_team_info),
                ]:
                    db.add(
                        RealMatchTeam(
                            realMatchID=real_match_id,
                            realTeamID=team_id,
                            realTeamUID=team_uid,
                            realTeamName=team_info[1],
                            realTeamShortName=team_info[2],
                            realTeamSide=side,
                            realTeamNumber=1 if side == "Home" else 2,
                            createdIn=task.start_time,
                            updatedIn=task.start_time,
                        )
                    )

        task.close(status=Task.COMPLETED if not task.errors else Task.ERROR)
        return task
