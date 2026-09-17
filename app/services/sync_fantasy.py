# ruff: noqa: BLE001  – broad Exception catches are intentional in sync handlers
"""Fantasy league synchronization service.

Syncs application-level fantasy data across Leagues, Divisions, Teams, and Matches.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.query import QueryService
from app.utils.tasks import Task


class SyncFantasyService:
    """Synchronize application-level fantasy data."""

    @staticmethod
    def sync_all(
        db: Session,
        real_competition_id: int | None = None,
    ) -> Task:
        """Sync all fantasy data (Leagues → Divisions → Teams → Matches).

        Args:
            db: Database session
            real_competition_id: RealCompetitionID to sync. If None, derived from current season.

        Returns:
            Task with aggregated results from all sync operations.
        """
        task = Task(
            name="sync_fantasy_all", status=Task.RUNNING, status_on_error=Task.ERROR
        )
        task.init_info("queries_executed", "rows_affected")

        ok = True

        try:
            # Sync Leagues
            if ok:
                sub = Task(
                    name="_sync_leagues",
                    status=Task.RUNNING,
                    status_on_error=Task.ERROR,
                )
                sub.init_info("queries_executed", "rows_affected")
                SyncFantasyService._sync_leagues(db, sub, real_competition_id)

                task.add_subtask(sub)
                task.inc("queries_executed", sub.info.get("queries_executed") or 0)
                task.inc("rows_affected", sub.info.get("rows_affected") or 0)
                ok = len(sub.errors) == 0

            # Sync Divisions
            if ok:
                sub = Task(
                    name="_sync_divisions",
                    status=Task.RUNNING,
                    status_on_error=Task.ERROR,
                )
                sub.init_info("queries_executed", "rows_affected")
                SyncFantasyService._sync_divisions(db, sub, real_competition_id)

                task.add_subtask(sub)
                task.inc("queries_executed", sub.info.get("queries_executed") or 0)
                task.inc("rows_affected", sub.info.get("rows_affected") or 0)
                ok = len(sub.errors) == 0

            # Sync Teams
            if ok:
                sub = Task(
                    name="_sync_teams", status=Task.RUNNING, status_on_error=Task.ERROR
                )
                sub.init_info("queries_executed", "rows_affected")
                SyncFantasyService._sync_teams(db, sub, real_competition_id)

                task.add_subtask(sub)
                task.inc("queries_executed", sub.info.get("queries_executed") or 0)
                task.inc("rows_affected", sub.info.get("rows_affected") or 0)
                ok = len(sub.errors) == 0

            # Sync Matches
            if ok:
                sub = Task(
                    name="_sync_matches",
                    status=Task.RUNNING,
                    status_on_error=Task.ERROR,
                )
                sub.init_info("queries_executed", "rows_affected")
                SyncFantasyService._sync_matches(db, sub, real_competition_id)

                task.add_subtask(sub)
                task.inc("queries_executed", sub.info.get("queries_executed") or 0)
                task.inc("rows_affected", sub.info.get("rows_affected") or 0)
                ok = len(sub.errors) == 0

        except Exception as e:
            task.add_error(str(e))

        task.close(status=Task.COMPLETED if not task.errors else Task.ERROR)
        return task

    @staticmethod
    def sync_league(db: Session, league_id: int) -> bool:
        """Sync all fantasy data for a single league (Leagues → Divisions → Teams → Matches).

        Args:
            db: Database session.
            league_id: LeagueID to sync.

        Returns:
            True if all steps succeeded, False if any step failed.
        """
        return (
            SyncFantasyService._sync_leagues(db, None, league_id=league_id)
            and SyncFantasyService._sync_divisions(db, None, league_id=league_id)
            and SyncFantasyService._sync_teams(db, None, league_id=league_id)
            and SyncFantasyService._sync_matches(db, None, league_id=league_id)
        )

    @staticmethod
    def sync_division(db: Session, division_id: int) -> bool:
        """Sync all fantasy data for a single division (Divisions → Teams → Matches).

        Args:
            db: Database session.
            division_id: DivisionID to sync.

        Returns:
            True if all steps succeeded, False if any step failed.
        """
        return (
            SyncFantasyService._sync_divisions(db, None, division_id=division_id)
            and SyncFantasyService._sync_teams(db, None, division_id=division_id)
            and SyncFantasyService._sync_matches(db, None, division_id=division_id)
        )

    @staticmethod
    def sync_team(db: Session, team_id: int) -> bool:
        """Sync all fantasy data for a single team (Teams → Matches).

        Args:
            db: Database session.
            team_id: TeamID to sync.

        Returns:
            True if all steps succeeded, False if any step failed.
        """
        return SyncFantasyService._sync_teams(
            db, None, team_id=team_id
        ) and SyncFantasyService._sync_matches(db, None, team_id=team_id)

    @staticmethod
    def _sync_leagues(
        db: Session,
        task: Task | None,
        real_competition_id: int | None = None,
        league_id: int | None = None,
    ) -> bool:
        """Sync Leagues with RealCompetitions data.

        Copies baseRealCompetitionID, extraRealCompetitionID, season, totalTeams,
        and availableTeams from RealCompetitions/Divisions/Teams into Leagues.

        Args:
            db: Database session.
            task: Task to record query counts and errors into. Pass None to skip tracking.
            real_competition_id: Restrict to leagues linked to this competition's base. If None, all leagues.
            league_id: Restrict to this specific league. If None, all leagues.

        Returns:
            True on success, False if a required competition lookup fails or an exception is raised.
        """
        ok = True
        try:
            # Build WHERE clause based on provided parameters
            where_conditions = []
            params = {}

            if real_competition_id:
                base_comp_id = QueryService.get_base_competition_id(
                    db, real_competition_id
                )
                if not base_comp_id:
                    if task:
                        task.add_error("Could not determine realCompetitionID")
                        task.close()
                    return False
                where_conditions.append(
                    "`rc`.`baseRealCompetitionID` = :baseRealCompetitionID"
                )
                params["baseRealCompetitionID"] = base_comp_id

            if league_id:
                where_conditions.append("`lg`.`leagueID` = :leagueID")
                params["leagueID"] = league_id

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            # Query #1: Update Leagues with competition data
            SyncFantasyService._exec(
                db,
                task,
                "Leagues_from_RealCompetitions(upd)",
                f"""
                UPDATE `Leagues` `lg`
                   INNER JOIN `RealCompetitions` `rc` ON `rc`.`realCompetitionID` = `rc`.`baseRealCompetitionID`
                   INNER JOIN (SELECT `leagueID`,
                                      SUM(`numTeams`) AS `totalTeams`
                                  FROM `Divisions`
                                  GROUP BY `leagueID`) `dv` ON `dv`.`leagueID` = `lg`.`leagueID`
                   INNER JOIN (SELECT `leagueID`,
                                      SUM(IF(`userID` IS NULL, 1, 0)) AS `availableTeams`
                                  FROM `Teams`
                                  GROUP BY `leagueID`) `tm` ON `tm`.`leagueID` = `lg`.`leagueID`
                   SET `lg`.`baseRealCompetitionID` = `rc`.`baseRealCompetitionID`,
                       `lg`.`extraRealCompetitionID` = `rc`.`extraRealCompetitionID`,
                       `lg`.`season` = `rc`.`realCompetitionSeasonId`,
                       `lg`.`totalTeams` = `dv`.`totalTeams`,
                       `lg`.`availableTeams` = `tm`.`availableTeams`
                   WHERE {where_clause}
            """,
                params,
            )

        except Exception as e:
            ok = False
            if task:
                task.add_error(str(e))

        if task:
            task.close(status=Task.COMPLETED if not task.errors else Task.ERROR)
        return ok

    @staticmethod
    def _sync_divisions(
        db: Session,
        task: Task | None,
        real_competition_id: int | None = None,
        league_id: int | None = None,
        division_id: int | None = None,
    ) -> bool:
        """Sync Divisions with Leagues data.

        Copies competition IDs, league hierarchy, season, and team counts from Leagues/Teams
        into Divisions.

        Args:
            db: Database session.
            task: Task to record query counts and errors into. Pass None to skip tracking.
            real_competition_id: Restrict to divisions whose league is linked to this competition's base. If None, all divisions.
            league_id: Restrict to divisions in this league. If None, all divisions.
            division_id: Restrict to this specific division. If None, all divisions.

        Returns:
            True on success, False if a required competition lookup fails or an exception is raised.
        """

        ok = True
        try:
            # Build WHERE clause based on provided parameters
            where_conditions = []
            params = {}

            if real_competition_id:
                base_comp_id = QueryService.get_base_competition_id(
                    db, real_competition_id
                )
                if not base_comp_id:
                    if task:
                        task.add_error("Could not determine realCompetitionID")
                        task.close()
                    return False
                where_conditions.append(
                    "`lg`.`baseRealCompetitionID` = :baseRealCompetitionID"
                )
                params["baseRealCompetitionID"] = base_comp_id

            if league_id:
                where_conditions.append("`dv`.`leagueID` = :leagueID")
                params["leagueID"] = league_id

            if division_id:
                where_conditions.append("`dv`.`divisionID` = :divisionID")
                params["divisionID"] = division_id

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            # Query #1: Update Divisions with Leagues data
            SyncFantasyService._exec(
                db,
                task,
                "Divisions_from_Leagues(upd)",
                f"""
                UPDATE `Divisions` `dv`
                   LEFT OUTER JOIN `Leagues` `lg` ON `lg`.`leagueID` = `dv`.`leagueID`
                   LEFT OUTER JOIN (SELECT `divisionID`,
                                           SUM(IF(`userID` IS NULL, 1, 0)) AS `availableTeams`
                                       FROM `Teams`
                                       GROUP BY `divisionID`) `tm` ON `tm`.`divisionID` = `dv`.`divisionID`
                   SET `dv`.`baseRealCompetitionID` = `lg`.`baseRealCompetitionID`,
                       `dv`.`extraRealCompetitionID` = `lg`.`extraRealCompetitionID`,
                       `dv`.`leagueID` = `lg`.`leagueID`,
                       `dv`.`commissionerID` = `lg`.`commissionerID`,
                       `dv`.`prevLeagueID` = `lg`.`prevLeagueID`,
                       `dv`.`nextLeagueID` = `lg`.`nextLeagueID`,
                       `dv`.`season` = `lg`.`season`,
                       `dv`.`seasonNum` = `lg`.`seasonNum`,
                       `dv`.`totalTeams` = `lg`.`totalTeams`,
                       `dv`.`availableTeams` = `tm`.`availableTeams`
                   WHERE {where_clause}
            """,
                params,
            )

        except Exception as e:
            ok = False
            if task:
                task.add_error(str(e))
        if task:
            task.close(status=Task.COMPLETED if not task.errors else Task.ERROR)
        return ok

    @staticmethod
    def _sync_teams(
        db: Session,
        task: Task | None,
        real_competition_id: int | None = None,
        league_id: int | None = None,
        division_id: int | None = None,
        team_id: int | None = None,
    ) -> bool:
        """Sync Teams with Divisions data.

        Copies competition IDs, league/division hierarchy, season, match counts, and
        matchDayMapKey from Divisions into Teams.

        Args:
            db: Database session.
            task: Task to record query counts and errors into. Pass None to skip tracking.
            real_competition_id: Restrict to teams whose division is linked to this competition's base. If None, all teams.
            league_id: Restrict to teams in this league. If None, all teams.
            division_id: Restrict to teams in this division. If None, all teams.
            team_id: Restrict to this specific team. If None, all teams.

        Returns:
            True on success, False if a required competition lookup fails or an exception is raised.
        """

        ok = True
        try:
            # Build WHERE clause based on provided parameters
            where_conditions = []
            params = {}

            if real_competition_id:
                base_comp_id = QueryService.get_base_competition_id(
                    db, real_competition_id
                )
                if not base_comp_id:
                    if task:
                        task.add_error("Could not determine realCompetitionID")
                        task.close()
                    return False
                where_conditions.append(
                    "`tm`.`baseRealCompetitionID` = :baseRealCompetitionID"
                )
                params["baseRealCompetitionID"] = base_comp_id

            if league_id:
                where_conditions.append("`tm`.`leagueID` = :leagueID")
                params["leagueID"] = league_id

            if division_id:
                where_conditions.append("`tm`.`divisionID` = :divisionID")
                params["divisionID"] = division_id

            if team_id:
                where_conditions.append("`tm`.`teamID` = :teamID")
                params["teamID"] = team_id

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            # Query #1: Update Teams with Divisions data
            SyncFantasyService._exec(
                db,
                task,
                "Teams_from_Divisions(upd)",
                f"""
                UPDATE `Teams` `tm`
                   LEFT OUTER JOIN `Divisions` `dv` ON `tm`.`divisionID` = `dv`.`divisionID`
                   SET `tm`.`baseRealCompetitionID` = `dv`.`baseRealCompetitionID`,
                       `tm`.`extraRealCompetitionID` = `dv`.`extraRealCompetitionID`,
                       `tm`.`matchDayMapKey` = `dv`.`matchDayMapKey`,
                       `tm`.`leagueID` = `dv`.`leagueID`,
                       `tm`.`divisionID` = `dv`.`divisionID`,
                       `tm`.`commissionerID` = `dv`.`commissionerID`,
                       `tm`.`prevLeagueID` = `dv`.`prevLeagueID`,
                       `tm`.`nextLeagueID` = `dv`.`nextLeagueID`,
                       `tm`.`prevDivisionID` = `dv`.`prevDivisionID`,
                       `tm`.`nextDivisionID` = `dv`.`nextDivisionID`,
                       `tm`.`season` = `dv`.`season`,
                       `tm`.`seasonNum` = `dv`.`seasonNum`,
                       `tm`.`leagueMatches` = `dv`.`leagueMatches`,
                       `tm`.`divisionMatches` = `dv`.`divisionMatches`
                   WHERE {where_clause}
            """,
                params,
            )

        except Exception as e:
            ok = False
            if task:
                task.add_error(str(e))

        if task:
            task.close(status=Task.COMPLETED if not task.errors else Task.ERROR)
        return ok

    @staticmethod
    def _sync_matches(
        db: Session,
        task: Task | None,
        real_competition_id: int | None = None,
        league_id: int | None = None,
        division_id: int | None = None,
        team_id: int | None = None,
    ) -> bool:
        """Sync Matches and MatchTeams with Divisions/Teams data.

        Runs two queries:
          1. Matches ← Divisions: copies leagueID, divisionID, season, seasonNum.
          2. MatchTeams ← Teams: copies userID, teamID, teamName, matchDayMapKey, and teamSeeding
             (resolved from the team's seedingC1/C2/C3 based on the match's competitionType).

        Args:
            db: Database session.
            task: Task to record query counts and errors into. Pass None to skip tracking.
            real_competition_id: Restrict to matches for this competition (base + extra). If None, all matches.
            league_id: Restrict to matches in this league. If None, all matches.
            division_id: Restrict to matches in this division. If None, all matches.
            team_id: Restrict to matches in the division that contains this team. If None, all matches.

        Returns:
            True on success, False if a required competition lookup fails or an exception is raised.
        """

        ok = True
        try:
            # Build WHERE clause based on provided parameters
            where_conditions = []
            params = {}

            if real_competition_id:
                base_comp = QueryService.get_base_competition(db, real_competition_id)
                if not base_comp:
                    if task:
                        task.add_error("Could not determine realCompetitionID")
                        task.close()
                    return False
                where_conditions.append(
                    "`m`.`realCompetitionID` IN (:baseRealCompetitionID, :extraRealCompetitionID)"
                )
                params["baseRealCompetitionID"] = base_comp["baseRealCompetitionID"]
                params["extraRealCompetitionID"] = base_comp["extraRealCompetitionID"]

            if league_id:
                where_conditions.append("`m`.`leagueID` = :leagueID")
                params["leagueID"] = league_id

            if division_id:
                where_conditions.append("`m`.`divisionID` = :divisionID")
                params["divisionID"] = division_id

            if team_id:
                where_conditions.append(
                    "`m`.`divisionID` IN (SELECT `divisionID` FROM `Teams` WHERE `teamID` = :teamID)"
                )
                params["teamID"] = team_id

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            # Query #1: Update Matches with Divisions data
            SyncFantasyService._exec(
                db,
                task,
                "Matches_from_Divisions(upd)",
                f"""
                UPDATE `Matches` `m`
                   INNER JOIN `Divisions` `dv` ON `dv`.`divisionID` = `m`.`divisionID`
                   SET `m`.`leagueID` = `dv`.`leagueID`,
                       `m`.`divisionID` = `dv`.`divisionID`,
                       `m`.`season` = `dv`.`season`,
                       `m`.`seasonNum` = `dv`.`seasonNum`
                   WHERE {where_clause}
            """,
                params,
            )

            # Query #2: Update MatchTeams with Teams data
            SyncFantasyService._exec(
                db,
                task,
                "MatchTeams_from_Teams(upd)",
                f"""
                UPDATE `MatchTeams` `mt`
                   INNER JOIN `Matches` `m` ON `m`.`matchID` = `mt`.`matchID`
                   LEFT OUTER JOIN `Teams` `tm` ON `tm`.`teamID` = `mt`.`teamID`
                   SET  `mt`.`userID` = `tm`.`userID`,
                        `mt`.`teamID` = `tm`.`teamID`,
                        `mt`.`teamName` = `tm`.`teamName`,
                        `mt`.`matchDayMapKey` = `tm`.`matchDayMapKey`,
                        `mt`.`teamSeeding` = CASE `m`.`competitionType`
                                                 WHEN 1 THEN `tm`.`seedingC1`
                                                 WHEN 2 THEN `tm`.`seedingC2`
                                                 WHEN 3 THEN `tm`.`seedingC3`
                                                 ELSE NULL
                                             END
                   WHERE {where_clause}
            """,
                params,
            )

        except Exception as e:
            ok = False
            if task:
                task.add_error(str(e))

        if task:
            task.close(status=Task.COMPLETED if not task.errors else Task.ERROR)
        return ok

    @staticmethod
    def _exec(
        db: Session, task: Task | None, name: str, sql: str, params: dict | None = None
    ) -> None:
        """Execute one SQL statement and record its rowcount in the task.

        Increments task.info["queries_executed"] by 1, assigns result.rowcount to
        task.info[name], and adds that rowcount to task.info["rows_affected"].

        Args:
            db:     Database session.
            task:   Task whose info counters are updated.
            name:   Info-key to store the rowcount under (e.g. ``"base_fields(upd)"``).
            sql:    Raw SQL string (wrapped in ``text()`` internally).
            params: Bind parameters for the query. Defaults to ``{}`` when omitted.
        """
        if not params:
            params = {}
        result = db.execute(text(sql), params)
        if task:
            task.inc("queries_executed")
            task.inc("rows_affected", task.assign(name, result.rowcount))
