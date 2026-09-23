# ruff: noqa: BLE001  – broad except blocks are intentional diagnostic catches
"""F42 OPTA feed loader - loads data into the database."""

from datetime import datetime

from sqlalchemy import text, update
from sqlalchemy.orm import Session

from app.constants import DraftPositionConstants, RealMatchPeriod
from app.models import (
    Feed,
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
from app.utils.tasks import Task


class F42Loader:
    """Load F42 parsed data into the database."""

    @staticmethod
    def load_file(db: Session, feed: Feed, tmp_name: str | None = None) -> Feed:
        """Parse and load an F42 file into the database.

        Args:
            db: Database session
            feed: Feed log row
            tmp_name: Path to the temporary file containing the F42 data

        Returns:
            Feed row stamped with processing results.
        """
        from app.services.f_loader import FLoader  # lazy — avoids circular import

        # Parse the file — wrap so a parse error still stamps the Feed row
        file_path = tmp_name or feed.feedName
        task = Task(
            name=f"Load {F42Parser._FEED} file: {file_path}",
            status=Task.RUNNING,
            status_on_error=Task.ERROR,
        )
        task.init_info(
            "realCompetitionID", "realCompetitionSYMID", "realCompetitionSeasonId"
        )
        try:
            parsed_data = F42Parser.parse_file(file_path)
            task.add_subtask(parsed_data["task"])
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
            return FLoader.log_feed_end(db, feed, result=task)

        # Load competitions
        try:
            c_task, comp_data = F42Loader._load_competition(
                db, parsed_data["competition"]
            )
            task.add_subtask(c_task)
            if "realCompetitionID" not in comp_data:
                task.add_error("Competition not found — feed skipped")
                return FLoader.log_feed_end(db, feed, result=task)
            task.assign("realCompetitionID", comp_data["realCompetitionID"])
        except Exception as e:
            db.rollback()
            task.add_error(f"Error loading competition [{type(e).__name__}]: {e!s}")
            return FLoader.log_feed_end(db, feed, result=task)

        # Load teams
        team_id_mapping = {}
        try:
            t_task, team_id_mapping = F42Loader._load_teams(
                db, parsed_data["teams"], comp_data
            )
            task.add_subtask(t_task)
        except Exception as e:
            db.rollback()
            task.add_error(f"Error loading teams [{type(e).__name__}]: {e!s}")
            return FLoader.log_feed_end(db, feed, result=task)

        # Load players
        try:
            p_task = F42Loader._load_players(
                db, parsed_data["players"], comp_data, team_id_mapping
            )
            task.add_subtask(p_task)
        except Exception as e:
            db.rollback()
            task.add_error(f"Error loading players [{type(e).__name__}]: {e!s}")
            return FLoader.log_feed_end(db, feed, result=task)

        # Pre-load existing matches cache
        matches_cache = {}
        try:
            matches_cache = F42Loader._load_matches_cache(db, comp_data)
        except Exception as e:
            db.rollback()
            task.add_error(f"Error pre-loading matches [{type(e).__name__}]: {e!s}")
            return FLoader.log_feed_end(db, feed, result=task)

        # Build teams cache from loaded teams
        teams_cache = {}
        try:
            for team_data in parsed_data["teams"]:
                team_uid = team_data.get("realTeamUID")
                if team_uid in team_id_mapping:
                    # Query for team details
                    team_result = db.execute(
                        text("""
                        SELECT `realTeamID`,
                               `realTeamName`,
                               `realTeamShortName`
                           FROM `RealTeams`
                           WHERE `realCompetitionID` = :realCompetitionID
                             AND `realTeamUID` = :realTeamUID
                           LIMIT 1
                    """),
                        {
                            "realCompetitionID": comp_data["realCompetitionID"],
                            "realTeamUID": team_uid,
                        },
                    ).first()
                    if team_result:
                        teams_cache[team_uid] = list(team_result)
        except Exception as e:
            db.rollback()
            task.add_error(f"Error building teams cache [{type(e).__name__}]: {e!s}")
            return FLoader.log_feed_end(db, feed, result=task)

        # Load matches
        try:
            m_task = F42Loader._load_matches(
                db,
                parsed_data["matches"],
                matches_cache,
                teams_cache,
                comp_data,
            )
            task.add_subtask(m_task)
        except Exception as e:
            db.rollback()
            task.add_error(f"Error loading matches [{type(e).__name__}]: {e!s}")

        try:
            mds_result = F42Loader._save_mds(db, comp_data["realCompetitionID"])
            task.add_subtask(mds_result)
        except Exception as e:
            db.rollback()
            task.add_error(f"Error saving MDS data [{type(e).__name__}]: {e!s}")

        try:
            sync_result = F42Loader._sync(
                db, comp_data["realCompetitionID"], include_rtm=True
            )
            task.add_subtask(sync_result)
        except Exception as e:
            db.rollback()
            task.add_error(f"Error syncing data [{type(e).__name__}]: {e!s}")

        task.close(status=Task.COMPLETED if not task.errors else Task.ERROR)
        return FLoader.log_feed_end(db, feed, result=task)

    @staticmethod
    def _sync(db: Session, real_competition_id: int, include_rtm: bool = False) -> Task:
        # Each service gets its own commit+rollback so a dirty session from an
        # internal SQL failure (caught inside the service) never leaks out and
        # corrupts log_feed_end's final commit.
        task = Task(name="Sync", status=Task.RUNNING, status_on_error=Task.ERROR)

        try:
            sync_real = SyncRealService.sync_all(
                db, real_competition_id, include_rtm=include_rtm
            )
            db.commit()
            task.add_subtask(sync_real)
        except Exception as e:
            db.rollback()
            sub = Task(
                name="sync_real", status=Task.RUNNING, status_on_error=Task.ERROR
            )
            sub.add_error(f"[{type(e).__name__}]: {e!s}")
            sub.close()
            task.add_subtask(sub)

        try:
            sync_fantasy = SyncFantasyService.sync_all(db, real_competition_id)
            db.commit()
            task.add_subtask(sync_fantasy)
        except Exception as e:
            db.rollback()
            sub = Task(
                name="sync_fantasy", status=Task.RUNNING, status_on_error=Task.ERROR
            )
            sub.add_error(f"[{type(e).__name__}]: {e!s}")
            sub.close()
            task.add_subtask(sub)

        task.close(status=Task.COMPLETED if not task.errors else Task.ERROR)
        return task

    @staticmethod
    def _save_mds(db: Session, real_competition_id: int) -> Task:
        """_summary_

        Args:
            db (Session): _description_
            real_competition_id (int): _description_

        Returns:
            Task: _description_
        """
        return SaveMDS(db, real_competition_id).process()

    @staticmethod
    def _load_competition(
        db: Session, comp_data: dict
    ) -> tuple[Task, dict[str, str | int | datetime | None]]:
        """Look up a competition in RealCompetitions and stamp lastF42Date.

        Competitions are managed externally — this loader does not insert.
        """
        task = Task(
            name="Load Competition", status=Task.RUNNING, status_on_error=Task.ERROR
        )
        task.init_info("updated")
        # Query for existing competition
        row = (
            db.execute(
                text("""
                    SELECT `realCompetitionID`,
                           `baseRealCompetitionID`,
                           `extraRealCompetitionID`,
                           `realCompetitionUID`,
                           `realCompetitionCountry`,
                           `realCompetitionFirstMatchDay`,
                           `realCompetitionLastMatchDay`
                    FROM `RealCompetitions`
                    WHERE `realCompetitionSYMID` = :realCompetitionSYMID
                      AND `realCompetitionSeasonId` = :realCompetitionSeasonId
                    LIMIT 1
                """),
                {
                    "realCompetitionSYMID": comp_data["realCompetitionSYMID"],
                    "realCompetitionSeasonId": comp_data["realCompetitionSeasonId"],
                },
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
        db: Session, teams_data: list, comp_data: dict[str, str | int | datetime | None]
    ) -> tuple[Task, dict[str, int]]:
        """Load or update teams in RealTeams.

        Returns:
            Dictionary with inserted, updated counts and team_uid_mapping
        """
        task = Task(name="Load Teams", status=Task.RUNNING, status_on_error=Task.ERROR)
        task.init_info("inserted", "updated")
        team_uid_mapping = {}  # Map team uID to realTeamID for later use

        for team_data in teams_data:
            if not (team_data.get("realTeamUID") and team_data.get("realTeamName")):
                continue

            # Query for existing team
            result = db.execute(
                text("""
                    SELECT `realTeamID`
                    FROM `RealTeams`
                    WHERE `realCompetitionID` = :realCompetitionID
                      AND `realTeamUID` = :realTeamUID
                    LIMIT 1
                """),
                {
                    "realCompetitionID": comp_data["realCompetitionID"],
                    "realTeamUID": team_data["realTeamUID"],
                },
            ).first()

            if result:
                # Update existing
                db.execute(
                    update(RealTeam)
                    .where(RealTeam.realTeamID == result[0])
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
                team_uid_mapping[team_data["realTeamUID"]] = result[0]

        task.close(status=Task.COMPLETED if not task.errors else Task.ERROR)
        return (task, team_uid_mapping)

    @staticmethod
    def _load_players(
        db: Session,
        players_data: list,
        comp_data: dict,
        team_uid_mapping: dict,
    ) -> Task:
        """Load or update players in RealPlayers."""
        task = Task(
            name="Load Players", status=Task.RUNNING, status_on_error=Task.ERROR
        )
        task.init_info("inserted", "updated")

        def safe_int(value):
            try:
                return int(value) if value else None
            except (ValueError, TypeError):
                return None

        def safe_float(value):
            try:
                return float(value) if value else None
            except (ValueError, TypeError):
                return None

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
            result = db.execute(
                text("""
                    SELECT `realPlayerID`
                    FROM `RealPlayers`
                    WHERE `realCompetitionID` = :realCompetitionID
                      AND `realPlayerUID` = :realPlayerUID
                    LIMIT 1
                """),
                {
                    "realCompetitionID": comp_data["realCompetitionID"],
                    "realPlayerUID": player_data["realPlayerUID"],
                },
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
                    .where(RealPlayer.realPlayerID == result[0])
                    .values(
                        firstName=player_data.get("firstName"),
                        lastName=player_data.get("lastName"),
                        knownName=player_data.get("knownName"),
                        position=player_data.get("position"),
                        realPosition=player_data.get("realPosition"),
                        birthDate=safe_date(player_data.get("birthDate")),
                        weight=safe_float(player_data.get("weight")),
                        height=safe_float(player_data.get("height")),
                        jerseyNumber=safe_int(player_data.get("jerseyNumber")),
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
                        weight=safe_float(player_data.get("weight")),
                        height=safe_float(player_data.get("height")),
                        jerseyNumber=safe_int(player_data.get("jerseyNumber")),
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

        results = (
            db.execute(
                text("""
                    SELECT `m`.`realMatchID` AS `mID`,
                           `t1`.`realMatchTeamID` AS `mtID_1`,
                           `t2`.`realMatchTeamID` AS `mtID_2`,
                           `t1`.`realTeamUID` AS `tUID_1`,
                           `t2`.`realTeamUID` AS `tUID_2`
                    FROM `RealMatches` `m`
                    INNER JOIN `RealMatchTeams` `t1`
                        ON `m`.`realMatchID` = `t1`.`realMatchID`
                        AND `t1`.`realTeamNumber` = 1
                    INNER JOIN `RealMatchTeams` `t2`
                        ON `m`.`realMatchID` = `t2`.`realMatchID`
                        AND `t2`.`realTeamNumber` = 2
                    WHERE `m`.`realCompetitionID` = :realCompetitionID
                """),
                {"realCompetitionID": comp_data["realCompetitionID"]},
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
        matches_data: list,
        matches_cache: dict,
        teams_cache: dict,
        comp_data: dict,
    ) -> Task:
        """Load or update matches and match teams."""
        task = Task(
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
