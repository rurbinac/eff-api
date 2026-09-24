# ruff: noqa: BLE001  – broad except blocks are intentional diagnostic catches
"""F7 OPTA feed loader - loads single match detailed results."""

from datetime import datetime

from sqlalchemy import text, update
from sqlalchemy.orm import Session

from app.constants import RealMatchPeriod
from app.models import Feed, RealMatch, RealMatchTeam, RealStanding
from app.services.f7_events import load_booking, load_goal, load_substitution
from app.services.f7_parser import F7Parser
from app.services.f7_standings import calc_player_points, process_events
from app.utils.dt import utc_now
from app.utils.scalars import to_int
from app.utils.tasks import Task


class F7Loader:
    """Load F7 parsed data into the database (foundation layer for both quick and full modes)."""

    @staticmethod
    def load_file(
        db: Session, feed: Feed, tmp_name: str | None = None, quick_mode: bool = True
    ) -> Feed:
        """Parse and load an F7 file with mode-specific persistence.

        Args:
            db: Database session
            feed: Feed log row
            tmp_name: Path to the temporary file containing the F7 data
            quick_mode: True for quick mode, False for full mode

        Returns:
            Feed row stamped with processing results.
        """
        from app.services.f_loader import FLoader  # lazy — avoids circular import

        file_path = tmp_name or feed.feedName
        task = Task(
            name=f"Load F7 file: {file_path}",
            status=Task.RUNNING,
            status_on_error=Task.ERROR,
        )

        # Phase 1: Foundation layer (parse + build caches)
        foundation = None
        try:
            f_task, foundation = F7Loader._get_foundation(db, file_path)
            task.add_subtask(f_task)
        except Exception as e:
            task.add_error(f"Error in foundation [{type(e).__name__}]: {e!s}")
        finally:
            FLoader.delete_temp_file(tmp_name)

        if foundation is None or task.errors:
            task.close()
            return FLoader.log_feed_end(db, feed, result=task)

        # Phase 2: Process F7 data into in-memory structures
        processed_data = None
        try:
            p_task, processed_data = F7Loader._process_f7_data(
                foundation["parsed_data"],
                foundation["players_cache"],
            )
            task.add_subtask(p_task)
        except Exception as e:
            task.add_error(f"Error processing F7 data [{type(e).__name__}]: {e!s}")

        if processed_data is None or task.errors:
            task.close()
            return FLoader.log_feed_end(db, feed, result=task)

        # Phase 3: Persist based on mode
        if quick_mode:
            s_task = F7Loader._save_quick_mode(db, foundation, processed_data)
        else:
            s_task = F7Loader._save_full_mode(db, foundation, processed_data)
        task.add_subtask(s_task)

        task.close(status=Task.COMPLETED if not task.errors else Task.ERROR)
        return FLoader.log_feed_end(db, feed, result=task)

    @staticmethod
    def _get_foundation(db: Session, file_path: str) -> tuple[Task, dict | None]:
        """Get foundation layer data (parse file + build caches).

        Returns:
            (task, foundation_dict) or (task, None) if a critical step failed.
        """
        task = Task(name="Foundation", status=Task.RUNNING, status_on_error=Task.ERROR)

        # Parse the file
        try:
            parsed_data = F7Parser.parse_file(file_path)
            task.add_subtask(parsed_data["task"])
        except Exception as e:
            task.add_error(f"Error parsing file [{type(e).__name__}]: {e!s}")
            task.close()
            return task, None

        # Get RealCompetitions record — enriches the parser competition dict with DB data
        try:
            competition = F7Loader._get_real_competition(db, parsed_data["competition"])
        except Exception as e:
            task.add_error(
                f"Failed to get RealCompetitions [{type(e).__name__}]: {e!s}"
            )
            task.close()
            return task, None

        real_competition_id = competition["realCompetitionID"]

        # Build teams cache
        try:
            teams_cache = F7Loader._build_teams_cache(
                db, real_competition_id, parsed_data["match_data"]
            )
        except Exception as e:
            task.add_error(f"Failed to build teams cache [{type(e).__name__}]: {e!s}")
            task.close()
            return task, None

        # Get match IDs
        try:
            match_ids = F7Loader._get_match_ids(db, real_competition_id, teams_cache)
            if not match_ids:
                task.add_error("Match not found in database")
                task.close()
                return task, None
        except Exception as e:
            task.add_error(f"Failed to get match IDs [{type(e).__name__}]: {e!s}")
            task.close()
            return task, None

        # Build players cache with lineup data
        try:
            player_lineup = parsed_data["match_data"].get("player_lineup", {})
            match_time = parsed_data["match_data"].get("realMatchTime")
            players_cache = F7Loader._build_players_cache(
                db,
                real_competition_id,
                parsed_data["players"],
                player_lineup,
                match_time,
            )
        except Exception as e:
            task.add_error(f"Failed to build players cache [{type(e).__name__}]: {e!s}")
            task.close()
            return task, None

        # Populate oppositeRealTeamUID on each player — required by _process_goal
        # to call _process_match_clean_sheet on the correct team's players
        team_uids = list(teams_cache.keys())
        for player_data in players_cache.values():
            own = player_data.get("realTeamUID")
            player_data["oppositeRealTeamUID"] = next(
                (uid for uid in team_uids if uid != own), None
            )

        task.close(status=Task.COMPLETED)
        return task, {
            "parsed_data": parsed_data,
            "competition": competition,
            "match_ids": match_ids,
            "teams_cache": teams_cache,
            "players_cache": players_cache,
        }

    @staticmethod
    def _process_f7_data(
        parsed_data: dict,
        players_cache: dict,
    ) -> tuple[Task, dict]:
        """Process F7 data into in-memory structures.

        Returns:
            (task, processed_data) where processed_data contains:
            - match_data: raw match data from parser
            - match_events: sorted list of events with eventKey for deduplication
            - standings_data: player standings/performance data
        """
        task = Task(
            name="Process F7 Data", status=Task.RUNNING, status_on_error=Task.ERROR
        )
        task.init_info("goals", "bookings", "substitutions")

        match_data = parsed_data.get("match_data", {})
        events_cache = []

        for goal_data in match_data.get("goals", []):
            load_goal(events_cache, goal_data["element"], goal_data["team_uid"])
            task.inc("goals")

        for booking_data in match_data.get("bookings", []):
            load_booking(
                events_cache, booking_data["element"], booking_data["team_uid"]
            )
            task.inc("bookings")

        for sub_data in match_data.get("substitutions", []):
            load_substitution(events_cache, sub_data["element"], sub_data["team_uid"])
            task.inc("substitutions")

        # Sort events by eventKey (period, time, timestamp, class)
        events_cache.sort(key=lambda e: e.get("eventKey", ""))

        match_time_str = match_data.get("realMatchTime")
        try:
            match_time = int(match_time_str) if match_time_str else None
        except (ValueError, TypeError):
            match_time = None

        if match_time:
            players_cache = process_events(players_cache, events_cache, match_time)

        players_cache = calc_player_points(players_cache)

        task.close(status=Task.COMPLETED if not task.errors else Task.ERROR)
        return task, {
            "match_data": match_data,
            "match_events": events_cache,
            "standings_data": players_cache,
        }

    @staticmethod
    def _save_quick_mode(db: Session, foundation: dict, processed_data: dict) -> Task:
        """Save data in Quick mode (updates only).

        Quick mode updates:
        - RealMatches
        - RealMatchTeams
        - RealStandings (teams and players)
        """
        task = Task(
            name="Save Quick Mode", status=Task.RUNNING, status_on_error=Task.ERROR
        )
        task.init_info(
            "matches_updated",
            "match_teams_updated",
            "standings_updated",
            "players_standings_updated",
        )

        match_ids = foundation["match_ids"]
        match_data = processed_data["match_data"]

        try:
            F7Loader._update_match_quick_mode(db, match_ids, match_data)
            task.inc("matches_updated")
        except Exception as e:
            task.add_error(f"RealMatches update failed [{type(e).__name__}]: {e!s}")

        try:
            teams_result = F7Loader._update_match_teams_quick_mode(
                db, match_ids, match_data, foundation["teams_cache"]
            )
            task.assign("match_teams_updated", teams_result.get("teams_updated", 0))
        except Exception as e:
            task.add_error(f"RealMatchTeams update failed [{type(e).__name__}]: {e!s}")

        # Parse match day once for both standings updates
        real_match_day = None
        try:
            real_match_day = int(
                foundation["competition"].get("realCompetitionMatchDay")
            )
        except (ValueError, TypeError):
            pass

        if real_match_day:
            try:
                standings_result = F7Loader._update_standings_quick_mode(
                    db,
                    match_ids,
                    match_data,
                    foundation["teams_cache"],
                    foundation["competition"]["realCompetitionID"],
                    real_match_day,
                )
                task.assign(
                    "standings_updated", standings_result.get("standings_updated", 0)
                )
            except Exception as e:
                task.add_error(
                    f"RealStandings team update failed [{type(e).__name__}]: {e!s}"
                )

            try:
                player_result = F7Loader._update_player_standings_quick_mode(
                    db,
                    match_ids,
                    match_data,
                    foundation["teams_cache"],
                    processed_data["standings_data"],
                    foundation["competition"]["realCompetitionID"],
                    real_match_day,
                )
                task.assign(
                    "players_standings_updated", player_result.get("players_updated", 0)
                )
            except Exception as e:
                task.add_error(
                    f"RealStandings player update failed [{type(e).__name__}]: {e!s}"
                )

        task.close(status=Task.COMPLETED if not task.errors else Task.ERROR)
        return task

    @staticmethod
    def _save_full_mode(db: Session, _foundation: dict, _processed_data: dict) -> Task:
        """Save data in Full mode (complete updates). Not yet implemented."""
        task = Task(
            name="Save Full Mode", status=Task.RUNNING, status_on_error=Task.ERROR
        )
        task.add_error("Full mode implementation pending")
        task.close()
        return task

    @staticmethod
    def _get_real_competition(db: Session, competition: dict) -> dict:
        """Look up RealCompetitions and return the competition dict enriched with DB data.

        Merges the DB row (realCompetitionID, baseRealCompetitionID, etc.) into
        the parser-supplied competition dict so callers have a single source of truth.

        Note: F7 feeds carry a short numeric season_id (e.g. "7") that does not
        match the season identifier stored by F42 feeds.  We therefore look up by
        realCompetitionSYMID alone and take the most recently updated record.
        """
        symid = competition.get("realCompetitionSYMID")

        if not symid:
            raise ValueError("Missing realCompetitionSYMID in competition data")

        row = (
            db.execute(
                text("""
                    SELECT `realCompetitionID`,
                           `baseRealCompetitionID`,
                           `extraRealCompetitionID`,
                           `realCompetitionUID`,
                           `realCompetitionSeasonId`,
                           `realCompetitionCountry`,
                           `realCompetitionFirstMatchDay`,
                           `realCompetitionLastMatchDay`
                    FROM `RealCompetitions`
                    WHERE `realCompetitionSYMID` = :symid
                    ORDER BY `updatedIn` DESC
                    LIMIT 1
                """),
                {"symid": symid},
            )
            .mappings()
            .first()
        )

        if not row:
            raise ValueError(f"RealCompetition not found for symid={symid!r}")

        # Merge: DB data takes precedence for shared keys (e.g. realCompetitionUID)
        return dict(row) | competition

    @staticmethod
    def _build_teams_cache(
        db: Session, real_competition_id: int, match_data: dict
    ) -> dict:
        """Build teams cache from RealTeams table."""
        home_team_uid = match_data.get("home_team_ref")
        away_team_uid = match_data.get("away_team_ref")

        if not (home_team_uid and away_team_uid):
            raise ValueError("Missing home or away team reference in match data")

        results = (
            db.execute(
                text("""
                    SELECT `realTeamID`,
                           `realTeamUID`,
                           `realTeamMemberKey`,
                           `realTeamName`,
                           `realTeamShortName`
                    FROM `RealTeams`
                    WHERE `realCompetitionID` = :comp_id
                      AND (`realTeamUID` = :home_uid
                           OR `realTeamUID` = :away_uid)
                """),
                {
                    "comp_id": real_competition_id,
                    "home_uid": home_team_uid,
                    "away_uid": away_team_uid,
                },
            )
            .mappings()
            .all()
        )

        teams_cache = {}
        for row in results:
            teams_cache[row["realTeamUID"]] = {
                "realTeamID": row["realTeamID"],
                "realTeamMemberKey": row["realTeamMemberKey"],
                "realTeamName": row["realTeamName"],
                "realTeamShortName": row["realTeamShortName"],
            }

        # Add score and side from match data
        teams_cache[home_team_uid]["score"] = match_data.get("home_score")
        teams_cache[home_team_uid]["side"] = "Home"
        teams_cache[away_team_uid]["score"] = match_data.get("away_score")
        teams_cache[away_team_uid]["side"] = "Away"

        return teams_cache

    @staticmethod
    def _get_match_ids(
        db: Session, real_competition_id: int, teams_cache: dict
    ) -> dict | None:
        """Get RealMatch and RealMatchTeam IDs."""
        if len(teams_cache) < 2:
            return None

        home_uid = next(
            (uid for uid, d in teams_cache.items() if d.get("side") == "Home"), None
        )
        away_uid = next(
            (uid for uid, d in teams_cache.items() if d.get("side") == "Away"), None
        )
        if not home_uid or not away_uid:
            return None

        result = db.execute(
            text("""
                SELECT `m`.`realMatchID` AS `mID`,
                       `t1`.`realMatchTeamID` AS `mtID_Home`,
                       `t2`.`realMatchTeamID` AS `mtID_Away`
                FROM `RealMatches` `m`
                INNER JOIN `RealMatchTeams` `t1`
                    ON `m`.`realMatchID` = `t1`.`realMatchID`
                    AND `t1`.`realTeamNumber` = 1
                INNER JOIN `RealMatchTeams` `t2`
                    ON `m`.`realMatchID` = `t2`.`realMatchID`
                    AND `t2`.`realTeamNumber` = 2
                WHERE `m`.`realCompetitionID` = :comp_id
                  AND `t1`.`realTeamUID` = :home_uid
                  AND `t2`.`realTeamUID` = :away_uid
                LIMIT 1
            """),
            {
                "comp_id": real_competition_id,
                "home_uid": home_uid,
                "away_uid": away_uid,
            },
        ).first()

        if not result:
            return None

        return {
            "realMatchID": result[0],
            "realMatchTeamID_Home": result[1],
            "realMatchTeamID_Away": result[2],
        }

    @staticmethod
    def _build_players_cache(
        db: Session,
        real_competition_id: int,
        players: dict,
        player_lineup: dict | None = None,
        match_time: int | None = None,
    ) -> dict:
        """Build players cache from RealPlayers table and PlayerLineUp data."""
        # Start with player data from XML
        players_cache = {}
        for player_uid, player_data in players.items():
            players_cache[player_uid] = {
                "realPlayerUID": player_uid,
                "realTeamMemberKey": None,
                "realTeamUID": player_data.get("realTeamUID"),
                "firstName": player_data.get("firstName"),
                "lastName": player_data.get("lastName"),
                "knownName": player_data.get("knownName"),
                "position": player_data.get("position"),
            }

        # Enrich with database data
        if players_cache:
            player_uids = list(players_cache.keys())

            # Build IN clause for query
            placeholders = ",".join([f":uid_{i}" for i in range(len(player_uids))])
            params = {f"uid_{i}": uid for i, uid in enumerate(player_uids)}
            params["comp_id"] = real_competition_id

            results = (
                db.execute(
                    text(f"""
                        SELECT `realPlayerID`,
                               `realPlayerUID`,
                               `realTeamMemberKey`,
                               `draftPosition`
                        FROM `RealPlayers`
                        WHERE `realCompetitionID` = :comp_id
                          AND `realPlayerUID` IN ({placeholders})
                    """),
                    params,
                )
                .mappings()
                .all()
            )

            for row in results:
                player_uid = row["realPlayerUID"]
                if player_uid in players_cache:
                    players_cache[player_uid]["realPlayerID"] = row["realPlayerID"]
                    players_cache[player_uid]["realTeamMemberKey"] = row[
                        "realTeamMemberKey"
                    ]
                    players_cache[player_uid]["draftPosition"] = row["draftPosition"]
                else:
                    # Player from database not yet in cache, add them
                    players_cache[player_uid] = {
                        "realPlayerUID": player_uid,
                        "realPlayerID": row["realPlayerID"],
                        "realTeamMemberKey": row["realTeamMemberKey"],
                        "draftPosition": row["draftPosition"],
                    }

        # Enrich with PlayerLineUp data
        if player_lineup:
            for player_ref, lineup_info in player_lineup.items():
                if player_ref in players_cache:
                    status = lineup_info.get("status")
                    shirt_number = lineup_info.get("shirtNumber")
                    formation_place = lineup_info.get("formationPlace")

                    players_cache[player_ref]["status"] = status
                    players_cache[player_ref]["formationPlace"] = formation_place
                    players_cache[player_ref]["shirtNumber"] = shirt_number

                    # Initialize performance tracking fields that are in RealStandings
                    players_cache[player_ref]["matchTimePlayed"] = 0
                    players_cache[player_ref]["matchGamePlayed"] = 0
                    players_cache[player_ref]["matchGoals"] = 0
                    players_cache[player_ref]["matchAssists"] = 0
                    players_cache[player_ref]["matchYellowCards"] = 0
                    players_cache[player_ref]["matchRedCards"] = 0
                    players_cache[player_ref]["matchGoalsConceded"] = 0
                    players_cache[player_ref]["matchCleanSheet"] = 0
                    players_cache[player_ref]["matchPointsL1Played"] = 0
                    players_cache[player_ref]["matchPointsL1GoalsAllowed"] = 0
                    players_cache[player_ref]["matchPointsL1CleanSheet"] = 0
                    players_cache[player_ref]["matchPointsL1Cards"] = 0
                    players_cache[player_ref]["matchPointsL1Goals"] = 0
                    players_cache[player_ref]["matchPointsL1Assists"] = 0
                    players_cache[player_ref]["matchPointsL1OwnGoals"] = 0

                    # Initialize other performance tracking fields
                    players_cache[player_ref]["_ownGoals"] = 0
                    players_cache[player_ref]["_secondYellowCards"] = 0
                    players_cache[player_ref]["_straightRedCards"] = 0

                    # Calculate playing time and flags based on status
                    if status == "Start":
                        # Player started the match
                        # - Adjust RealStandings fields
                        players_cache[player_ref]["matchTimePlayed"] = match_time
                        players_cache[player_ref]["matchGamePlayed"] = 1
                        players_cache[player_ref]["matchCleanSheet"] = 1
                        # - Create the other fields
                        players_cache[player_ref]["_timeIn"] = 0
                        players_cache[player_ref]["_timeOut"] = match_time
                        players_cache[player_ref]["_startedGame"] = 1
                        players_cache[player_ref]["_finishedGame"] = 1
                        players_cache[player_ref]["_fullGame"] = 1
                    else:
                        # Player is a substitute
                        # - Create the other fields
                        players_cache[player_ref]["_timeIn"] = None
                        players_cache[player_ref]["_timeOut"] = None
                        players_cache[player_ref]["_startedGame"] = 0
                        players_cache[player_ref]["_finishedGame"] = 0
                        players_cache[player_ref]["_fullGame"] = 0

        return players_cache

    @staticmethod
    def _fmt_date(raw: str | None) -> datetime | None:
        """Convert OPTA date string to a naive datetime.

        Handles the compact format used in F7 XML:
            20260913T163000+0100  ->  datetime(2026, 9, 13, 16, 30, 0)
            20260913T163000Z      ->  datetime(2026, 9, 13, 16, 30, 0)

        The timezone offset is discarded; the value is stored as-is (local kick-off time).
        """
        if not raw or "T" not in raw:
            return None
        try:
            date_part = raw.split("T")[0]
            time_part = raw.split("T")[1].split("+")[0].split("-")[0].split("Z")[0]
            return datetime(
                int(date_part[:4]),
                int(date_part[4:6]),
                int(date_part[6:8]),
                int(time_part[:2]),
                int(time_part[2:4]),
                int(time_part[4:6]),
            )
        except Exception:
            return None

    @staticmethod
    def _update_match_quick_mode(
        db: Session, match_ids: dict, match_data: dict
    ) -> dict:
        """Update RealMatches with F7 data in Quick mode.

        Args:
            db: Database session
            match_ids: Dict with realMatchID from foundation layer
            match_data: Parsed match data from F7

        Returns:
            Dict with update status and count
        """
        now = utc_now()

        # Extract and normalize period data
        period = RealMatchPeriod.normalize(match_data.get("realMatchPeriod"))
        real_match_status = RealMatchPeriod.to_match_status(period)
        real_match_ended = RealMatchPeriod.to_match_ended(period)

        # Normalize date: 20260913T163000+0100 -> 2026-09-13 16:30:00
        match_date = F7Loader._fmt_date(match_data.get("realMatchDate"))

        # Extract attendance (convert to int or None)
        attendance = None
        attendance_str = match_data.get("realMatchAttendance")
        if attendance_str:
            try:
                attendance = int(attendance_str)
            except (ValueError, TypeError):
                pass


        # Update RealMatches
        db.execute(
            update(RealMatch)
            .where(RealMatch.realMatchID == match_ids["realMatchID"])
            .values(
                realMatchStatus=real_match_status,
                realMatchType=match_data.get("realMatchType"),
                realMatchPeriod=period,
                realMatchRealPeriod=match_data.get("realMatchPeriod"),
                realMatchAttendance=attendance,
                realMatchDate=match_date,
                realMatchDateOffset=match_data.get("realMatchDateOffset"),
                realMatchResultType=match_data.get("realMatchResultType"),
                realMatchTime=to_int(match_data.get("realMatchTime")),
                realMatchFirstHalfTime=to_int(
                    match_data.get("realMatchFirstHalfTime")
                ),
                realMatchSecondHalfTime=to_int(
                    match_data.get("realMatchSecondHalfTime")
                ),
                realMatchEnded=real_match_ended,
                lastF7Date=now,
                lastFDate=now,
                updatedIn=now,
            )
        )

        return {"status": "updated", "match_id": match_ids["realMatchID"]}

    @staticmethod
    def _update_match_teams_quick_mode(
        db: Session, match_ids: dict, match_data: dict, teams_cache: dict
    ) -> dict:
        """Update RealMatchTeams with F7 data in Quick mode.

        Args:
            db: Database session
            match_ids: Dict with realMatchID, realMatchTeamID_Home, realMatchTeamID_Away
            match_data: Parsed match data from F7
            teams_cache: Teams cache with team info

        Returns:
            Dict with update status
        """
        now = utc_now()

        # Get scores
        home_score_str = match_data.get("home_score")
        away_score_str = match_data.get("away_score")

        home_score = None
        away_score = None
        try:
            home_score = int(home_score_str) if home_score_str else None
            away_score = int(away_score_str) if away_score_str else None
        except (ValueError, TypeError):
            pass

        # Prepare updates for both teams
        teams_to_update = [
            {
                "realMatchTeamID": match_ids["realMatchTeamID_Home"],
                "team_number": 1,
                "my_score": home_score,
                "other_score": away_score,
            },
            {
                "realMatchTeamID": match_ids["realMatchTeamID_Away"],
                "team_number": 2,
                "my_score": away_score,
                "other_score": home_score,
            },
        ]

        update_count = 0

        for team_update in teams_to_update:
            # Calculate points and result
            my_score = team_update["my_score"]
            other_score = team_update["other_score"]
            if my_score is None or other_score is None:
                points, result = 0, None
            elif my_score > other_score:
                points, result = 3, 1  # Win
            elif my_score < other_score:
                points, result = 0, -1  # Loss
            else:
                points, result = 1, 0  # Draw

            # Update RealMatchTeams
            db.execute(
                update(RealMatchTeam)
                .where(RealMatchTeam.realMatchTeamID == team_update["realMatchTeamID"])
                .values(
                    realTeamScore=my_score,
                    realTeamRealScore=my_score,
                    realTeamResult=result,
                    realTeamPoints=points,
                    updatedIn=now,
                )
            )

            update_count += 1

        return {"status": "updated", "teams_updated": update_count}

    @staticmethod
    def _update_standings_quick_mode(
        db: Session,
        match_ids: dict,
        match_data: dict,
        teams_cache: dict,
        real_competition_id: int,
        real_match_day: int,
    ) -> dict:
        """Update RealStandings for both teams with match results.

        Args:
            db: Database session
            match_ids: Dict with realMatchID from foundation
            match_data: Parsed match data with scores
            teams_cache: Teams cache with team info and scores
            real_competition_id: Competition ID
            real_match_day: Match day number

        Returns:
            Dict with update status
        """
        now = utc_now()

        # Get scores
        home_score = None
        away_score = None
        try:
            home_score = (
                int(match_data.get("home_score"))
                if match_data.get("home_score")
                else None
            )
            away_score = (
                int(match_data.get("away_score"))
                if match_data.get("away_score")
                else None
            )
        except (ValueError, TypeError):
            pass

        # Get match date and status
        match_date = F7Loader._fmt_date(match_data.get("realMatchDate"))
        match_time = match_data.get("realMatchTime")
        match_status = RealMatchPeriod.to_match_status(
            match_data.get("realMatchPeriod")
        )

        # Prepare updates for both teams
        teams_to_update = [
            {
                "side": "Home",
                "my_score": home_score,
                "other_score": away_score,
                "team_uid": None,  # Will be set below
            },
            {
                "side": "Away",
                "my_score": away_score,
                "other_score": home_score,
                "team_uid": None,  # Will be set below
            },
        ]

        # Map team UIDs to sides
        for team_uid, team_info in teams_cache.items():
            side = team_info.get("side")
            for team_update in teams_to_update:
                if team_update["side"] == side:
                    team_update["team_uid"] = team_uid

        update_count = 0

        for team_update in teams_to_update:
            team_uid = team_update["team_uid"]
            if not team_uid or team_uid not in teams_cache:
                continue

            team_info = teams_cache[team_uid]
            my_score = team_update["my_score"]
            other_score = team_update["other_score"]

            # Calculate match results
            match_won, match_draw, match_lost = 0, 0, 0
            if my_score is not None and other_score is not None:
                if my_score > other_score:
                    match_won = 1
                elif my_score < other_score:
                    match_lost = 1
                else:
                    match_draw = 1

            # Calculate match points
            match_points = 3 * match_won + match_draw

            # Update RealStandings
            db.execute(
                update(RealStanding)
                .where(
                    RealStanding.realCompetitionID == real_competition_id,
                    RealStanding.realCompetitionMatchDay == real_match_day,
                    RealStanding.realTeamMemberKey
                    == team_info.get("realTeamMemberKey"),
                )
                .values(
                    realMatchDate=match_date,
                    realMatchTime=match_time,
                    realMatchStatus=match_status,
                    realTeamScore=my_score,
                    oppositeRealTeamScore=other_score,
                    matchWon=match_won,
                    matchDraw=match_draw,
                    matchLost=match_lost,
                    matchPointsL1=match_points,
                    livePointsL1=match_points,
                    processed=1,
                    updatedIn=now,
                )
            )

            update_count += 1

        return {"status": "updated", "standings_updated": update_count}

    @staticmethod
    def _update_player_standings_quick_mode(
        db: Session,
        match_ids: dict,
        match_data: dict,
        teams_cache: dict,
        players_cache: dict,
        real_competition_id: int,
        real_match_day: int,
    ) -> dict:
        """Update RealStandings for all players with match performance.

        Args:
            db: Database session
            match_ids: Dict with realMatchID and realMatchTeamID values
            match_data: Parsed match data
            teams_cache: Teams cache with team info
            players_cache: Players cache with performance data
            real_competition_id: Competition ID
            real_match_day: Match day number

        Returns:
            Dict with update status
        """
        now = utc_now()

        # Get match data
        match_date = F7Loader._fmt_date(match_data.get("realMatchDate"))
        match_time = match_data.get("realMatchTime")
        match_status = RealMatchPeriod.to_match_status(
            match_data.get("realMatchPeriod")
        )

        # Build team info lookup (side -> team info)
        team_by_side = {}
        for team_uid, team_info in teams_cache.items():
            side = team_info.get("side")
            if side:
                team_by_side[side] = (team_uid, team_info)

        update_count = 0

        # Update RealStandings for each player
        for player_uid, player in players_cache.items():
            # Skip players without realTeamMemberKey
            if not player.get("realTeamMemberKey"):
                continue

            player_team_uid = player.get("realTeamUID")
            if not player_team_uid or player_team_uid not in teams_cache:
                continue

            team_info = teams_cache[player_team_uid]
            player_side = team_info.get("side")

            # Get opponent team info
            opponent_side = "Away" if player_side == "Home" else "Home"
            if opponent_side not in team_by_side:
                continue

            opponent_uid, opponent_info = team_by_side[opponent_side]

            # Find the correct realMatchTeamID for this player's team
            real_match_team_id = None
            if player_side == "Home" and "realMatchTeamID_Home" in match_ids:
                real_match_team_id = match_ids["realMatchTeamID_Home"]
            elif player_side == "Away" and "realMatchTeamID_Away" in match_ids:
                real_match_team_id = match_ids["realMatchTeamID_Away"]

            if not real_match_team_id:
                continue

            # Build player names
            known_name = player.get("knownName")
            first_name = player.get("firstName", "")
            last_name = player.get("lastName", "")
            name = known_name if known_name else f"{first_name} {last_name}".strip()
            sort_name = (
                known_name if known_name else f"{last_name} {first_name}".strip()
            )

            # Calculate total points
            total_points = (
                player.get("matchPointsL1Played", 0)
                + player.get("matchPointsL1GoalsAllowed", 0)
                + player.get("matchPointsL1CleanSheet", 0)
                + player.get("matchPointsL1Cards", 0)
                + player.get("matchPointsL1Goals", 0)
                + player.get("matchPointsL1Assists", 0)
                + player.get("matchPointsL1OwnGoals", 0)
            )

            # Update RealStandings for player
            db.execute(
                update(RealStanding)
                .where(
                    RealStanding.realCompetitionID == real_competition_id,
                    RealStanding.realCompetitionMatchDay == real_match_day,
                    RealStanding.realTeamMemberKey == player["realTeamMemberKey"],
                )
                .values(
                    realMatchID=match_ids["realMatchID"],
                    realMatchTeamID=real_match_team_id,
                    realMatchDate=match_date,
                    realMatchTime=match_time,
                    realMatchStatus=match_status,
                    realTeamID=team_info["realTeamID"],
                    realTeamUID=player_team_uid,
                    realTeamName=team_info["realTeamName"],
                    realTeamShortName=team_info["realTeamShortName"],
                    realTeamScore=team_info["score"],
                    realTeamSide=player_side,
                    oppositeRealTeamID=opponent_info["realTeamID"],
                    oppositeRealTeamUID=opponent_uid,
                    oppositeRealTeamName=opponent_info["realTeamName"],
                    oppositeRealTeamShortName=opponent_info["realTeamShortName"],
                    oppositeRealTeamScore=opponent_info["score"],
                    realPlayerID=player.get("realPlayerID"),
                    realPlayerUID=player_uid,
                    firstName=first_name,
                    lastName=last_name,
                    knownName=known_name,
                    name=name,
                    sortName=sort_name,
                    matchTimePlayed=player.get("matchTimePlayed", 0),
                    matchGamePlayed=player.get("matchGamePlayed", 0),
                    matchGoals=player.get("matchGoals", 0),
                    matchAssists=player.get("matchAssists", 0),
                    matchYellowCards=player.get("matchYellowCards", 0),
                    matchRedCards=player.get("matchRedCards", 0),
                    matchGoalsConceded=player.get("matchGoalsConceded", 0),
                    matchCleanSheet=player.get("matchCleanSheet", 0),
                    matchDayPlayed=player.get("matchGamePlayed", 0),
                    matchPointsL1Played=player.get("matchPointsL1Played", 0),
                    matchPointsL1GoalsAllowed=player.get(
                        "matchPointsL1GoalsAllowed", 0
                    ),
                    matchPointsL1CleanSheet=player.get("matchPointsL1CleanSheet", 0),
                    matchPointsL1Cards=player.get("matchPointsL1Cards", 0),
                    matchPointsL1Goals=player.get("matchPointsL1Goals", 0),
                    matchPointsL1Assists=player.get("matchPointsL1Assists", 0),
                    matchPointsL1OwnGoals=player.get("matchPointsL1OwnGoals", 0),
                    matchPointsL1=total_points,
                    livePointsL1=total_points,
                    processed=1,
                    updatedIn=now,
                )
            )

            update_count += 1

        return {"status": "updated", "players_updated": update_count}
