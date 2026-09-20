# ruff: noqa: BLE001  – broad Exception catches are intentional in sync handlers
"""Real competition synchronization service.

Syncs Real* table data (RealCompetitions, RealTeams, RealPlayers, RealMatches, etc.)
across competitions and seasons.
"""

from collections.abc import Generator
from functools import cmp_to_key

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.constants import DraftPositionConstants, RealCompetitionConstants
from app.utils.dt import utc_now
from app.utils.sql_text import sql_insert, sql_update
from app.utils.tasks import Task


class SyncRealService:
    """Synchronize Real* table data."""

    @staticmethod
    def sync_all(db: Session, real_competition_id: int | None = None, include_rtm: bool = False) -> Task:
        """Sync all Real* data for a competition season.

        Runs in order: RealCompetitions → RealTeams (+ RealTeamMembers teams) →
        RealPlayers (+ RealTeamMembers players) → optionally RealTeamMembers standings
        and the copy-back to RealTeamMembers.

        Args:
            db: Database session.
            real_competition_id: RealCompetitionID to sync. If None, derived from
                the current base competition via QueryService.
            include_rtm: When True, also runs _sync_real_team_members (recalculates
                RealStandings) and _sync_real_standings (copies final standings back
                to RealTeamMembers). Expensive — intended for the weekly end-of-match-day
                run, not every F42 load. Defaults to False.

        Returns:
            Task with aggregated queries_executed and rows_affected across all sub-tasks.
        """
        task = Task(name="sync_all", status=Task.RUNNING, status_on_error=Task.ERROR)
        task.init_info("queries_executed", "rows_affected", default=0)

        ok = True

        try:
            # Derive real_competition_id if not provided
            from app.services import QueryService

            real_competition_id = QueryService.get_competition_id(
                db, real_competition_id
            )
            if not real_competition_id:
                task.add_error("Could not determine realCompetitionID")
                task.close(status=Task.ERROR)
                return task

            # Sync RealCompetitions
            if ok:
                sub = SyncRealService._sync_real_competitions(db)
                task.add_subtask(sub)
                task.inc("queries_executed", sub.info.get("queries_executed") or 0)
                task.inc("rows_affected", sub.info.get("rows_affected") or 0)
                ok = len(sub.errors) == 0

            # Sync RealTeams
            if ok:
                sub = SyncRealService._sync_real_teams(db, real_competition_id)
                task.add_subtask(sub)
                task.inc("queries_executed", sub.info.get("queries_executed") or 0)
                task.inc("rows_affected", sub.info.get("rows_affected") or 0)
                ok = len(sub.errors) == 0

            # Sync RealPlayers
            if ok:
                sub = SyncRealService._sync_real_players(db, real_competition_id)
                task.add_subtask(sub)
                task.inc("queries_executed", sub.info.get("queries_executed") or 0)
                task.inc("rows_affected", sub.info.get("rows_affected") or 0)
                ok = len(sub.errors) == 0

            # Sync RealTeamMembers
            if ok and include_rtm:
                sub = SyncRealService._sync_real_team_members(db, real_competition_id)
                task.add_subtask(sub)
                task.inc("queries_executed", sub.info.get("queries_executed") or 0)
                task.inc("rows_affected", sub.info.get("rows_affected") or 0)
                ok = len(sub.errors) == 0

            # Sync standings back to RealTeamMembers
            if ok and include_rtm:
                sub = SyncRealService._sync_real_standings(db, real_competition_id)
                task.add_subtask(sub)
                task.inc("queries_executed", sub.info.get("queries_executed") or 0)
                task.inc("rows_affected", sub.info.get("rows_affected") or 0)
                ok = len(sub.errors) == 0

        except Exception as e:
            task.add_error(str(e))

        task.close(status=Task.COMPLETED if not task.errors else Task.ERROR)
        return task

    @staticmethod
    def _sync_real_competitions(db: Session) -> Task:
        """Internal: cross-link RealCompetitions and propagate changes to RealTeams and RealMatches.

        Sets baseRealCompetitionID / extraRealCompetitionID and
        prevRealCompetitionID / nextRealCompetitionID on every RealCompetitions row,
        then propagates the updated values to RealTeams and RealMatches.
        Invalidates the QueryService competition cache at the end.
        """
        task = Task(
            name="_sync_real_competitions",
            status=Task.RUNNING,
            status_on_error=Task.ERROR,
        )
        task.init_info("queries_executed", "rows_affected", default=0)

        try:
            # Query #1: Update baseID and extraID
            # Makes sure that all `RealCompetitions` rows have the correct values for:
            # - `baseRealCompetitionID`
            # - `extraRealCompetitionID`
            SyncRealService._exec(
                db,
                task,
                "base_and_extra(upd)",
                """
                UPDATE `RealCompetitions` `rc`
                   INNER JOIN `RealCompetitions` `rc_b`
                      ON `rc_b`.`realCompetitionSeasonId` = `rc`.`realCompetitionSeasonId`
                      AND `rc_b`.`realCompetitionSYMID` = :baseRealCompetitionSYMID
                   INNER JOIN `RealCompetitions` `rc_e`
                      ON `rc_e`.`realCompetitionSeasonId` = `rc`.`realCompetitionSeasonId`
                      AND `rc_e`.`realCompetitionSYMID` = :extraRealCompetitionSYMID
                   SET `rc`.`baseRealCompetitionID` = `rc_b`.`realCompetitionID`,
                       `rc`.`extraRealCompetitionID` = `rc_e`.`realCompetitionID`
            """,
                {
                    "baseRealCompetitionSYMID": RealCompetitionConstants.BASE_SYMID,
                    "extraRealCompetitionSYMID": RealCompetitionConstants.EXTRA_SYMID,
                },
            )

            # Query #2: Update prev and next
            # Makes sure that all `RealCompetitions` rows have the correct values for:
            # - `prevRealCompetitionID`
            # - `nextRealCompetitionID`
            SyncRealService._exec(
                db,
                task,
                "prev_and_next(upd)",
                """
                UPDATE `RealCompetitions` `c`
                   LEFT OUTER JOIN `RealCompetitions` `n`
                      ON `c`.`realCompetitionSYMID` = `n`.`realCompetitionSYMID`
                      AND CAST(`c`.`realCompetitionSeasonId` AS SIGNED) + 1 = CAST(`n`.`realCompetitionSeasonId` AS SIGNED)
                   LEFT OUTER JOIN `RealCompetitions` `p`
                      ON `c`.`realCompetitionSYMID` = `p`.`realCompetitionSYMID`
                      AND CAST(`c`.`realCompetitionSeasonId` AS SIGNED) - 1 = CAST(`p`.`realCompetitionSeasonId` AS SIGNED)
                   SET `c`.`prevRealCompetitionID` = `p`.`realCompetitionID`,
                       `c`.`nextRealCompetitionID` = `n`.`realCompetitionID`
            """,
            )

            # Query #3: Update `RealTeams`
            # Makes sure that the `RealCompetitions` values are propagated to `RealTeams`
            SyncRealService._exec(
                db,
                task,
                "to_RealTeams(upd)",
                """
                UPDATE `RealTeams` `t`
                   LEFT OUTER JOIN `RealCompetitions` `c` ON `c`.`realCompetitionID` = `t`.`realCompetitionID`
                   SET `t`.`realCompetitionUID` = `c`.`realCompetitionUID`,
                       `t`.`realCompetitionSYMID` = `c`.`realCompetitionSYMID`,
                       `t`.`realCompetitionSeasonId` = `c`.`realCompetitionSeasonId`,
                       `t`.`baseRealCompetitionID` = `c`.`baseRealCompetitionID`,
                       `t`.`extraRealCompetitionID` = `c`.`extraRealCompetitionID`
            """,
            )

            # Query #4: Update `RealMatches`
            # Makes sure that the `RealCompetitions` values are propagated to `RealMatches`
            SyncRealService._exec(
                db,
                task,
                "to_RealMatches(upd)",
                """
                UPDATE `RealMatches` `m`
                   LEFT OUTER JOIN `RealCompetitions` `c` ON `c`.`realCompetitionID` = `m`.`realCompetitionID`
                   SET `m`.`realCompetitionUID` = `c`.`realCompetitionUID`,
                       `m`.`realCompetitionSYMID` = `c`.`realCompetitionSYMID`,
                       `m`.`realCompetitionSeasonId` = `c`.`realCompetitionSeasonId`,
                       `m`.`realCompetitionFirstMatchDay` = `c`.`realCompetitionFirstMatchDay`,
                       `m`.`realCompetitionLastMatchDay` = `c`.`realCompetitionLastMatchDay`,
                       `m`.`baseRealCompetitionID` = `c`.`baseRealCompetitionID`,
                       `m`.`extraRealCompetitionID` = `c`.`extraRealCompetitionID`
            """,
            )

        except Exception as e:
            task.add_error(str(e))

        # Invalidate the base-competition cache — RealCompetitions rows may have changed.
        from app.services import QueryService

        QueryService.clear_real_competition_cache()

        task.close(status=Task.COMPLETED if not task.errors else Task.ERROR)
        return task

    @staticmethod
    def _sync_real_teams(db: Session, real_competition_id: int) -> Task:
        """Sync RealTeams, RealMatchTeams, and the team rows in RealTeamMembers.

        Runs six queries in order:
          1. Set baseRealTeamID, realTeamMemberKey, draftPosition, and lastFDate on RealTeams.
          2. Set prevRealTeamID / nextRealTeamID on RealTeams (cross-season links).
          3. Propagate team identity fields from RealTeams into RealMatchTeams.
          4. Insert new RealTeams rows into RealTeamMembers (base-season teams only).
          5. Write realTeamMemberID back from RealTeamMembers into RealTeams.
          6. Update existing RealTeamMembers rows with current RealTeams data.

        Args:
            db: Database session.
            real_competition_id: RealCompetitionID to sync.

        Returns:
            Task with queries_executed and rows_affected counts.
        """
        task = Task(
            name="_sync_real_teams", status=Task.RUNNING, status_on_error=Task.ERROR
        )
        task.init_info("queries_executed", "rows_affected", default=0)

        _dp = DraftPositionConstants.EPL_TEAM
        _dp_order = DraftPositionConstants.get_order(_dp)

        try:
            # Query #1: Set base fields for `RealTeams`
            SyncRealService._exec(
                db,
                task,
                "base_fields(upd)",
                """
                UPDATE `RealTeams` `t`
                   LEFT OUTER JOIN `RealTeams` `t1`
                      ON `t`.`baseRealCompetitionID` = `t1`.`realCompetitionID`
                      AND `t`.`realTeamUID` = `t1`.`realTeamUID`
                   SET `t`.`baseRealTeamID` = `t1`.`realTeamID`,
                       `t`.`baseRealTeamName` = `t1`.`realTeamName`,
                       `t`.`baseRealTeamShortName` = `t1`.`realTeamShortName`,
                       `t`.`realTeamMemberKey` = CONCAT('T', `t1`.`realTeamID`),
                       `t`.`draftPosition` = :draftPosition,
                       `t`.`draftPositionOrder` = :draftPositionOrder,
                       `t`.`lastFDate` = GREATEST(`t`.`lastF7Date`, `t`.`lastF42Date`)
                   WHERE `t`.`realCompetitionID` = :realCompetitionID
            """,
                {
                    "realCompetitionID": real_competition_id,
                    "draftPosition": _dp,
                    "draftPositionOrder": _dp_order,
                },
            )

            # Query #2: Update prev and next
            SyncRealService._exec(
                db,
                task,
                "prev_and_next(upd)",
                """
                UPDATE `RealTeams` `t`
                   LEFT OUTER JOIN `RealCompetitions` `c` ON `t`.`realCompetitionID` = `c`.`realCompetitionID`
                   LEFT OUTER JOIN `RealTeams` `t_p`
                      ON `t_p`.`realCompetitionID` = `c`.`prevRealCompetitionID`
                      AND `t_p`.`realTeamUID` = `t`.`realTeamUID`
                   LEFT OUTER JOIN `RealTeams` `t_n`
                      ON `t_n`.`realCompetitionID` = `c`.`nextRealCompetitionID`
                      AND `t_n`.`realTeamUID` = `t`.`realTeamUID`
                   SET `t`.`prevRealTeamID` = `t_p`.`realTeamID`,
                       `t`.`nextRealTeamID` = `t_n`.`realTeamID`
                   WHERE `t`.`realCompetitionID` = :realCompetitionID
            """,
                {"realCompetitionID": real_competition_id},
            )

            # Query #3: Sync team info to RealMatchTeams
            SyncRealService._exec(
                db,
                task,
                "to_RealMatchTeams(upd)",
                """
                UPDATE `RealMatchTeams` `mt`
                   INNER JOIN `RealMatches` `m` ON `m`.`realMatchID` = `mt`.`realMatchID`
                   LEFT OUTER JOIN `RealTeams` `t` ON `t`.`realTeamID` = `mt`.`realTeamID`
                   SET `mt`.`realTeamMemberID` = `t`.`realTeamMemberID`,
                       `mt`.`realTeamMemberKey` = `t`.`realTeamMemberKey`,
                       `mt`.`realTeamUID` = `t`.`realTeamUID`,
                       `mt`.`realTeamName` = `t`.`realTeamName`,
                       `mt`.`realTeamShortName` = `t`.`realTeamShortName`,
                       `mt`.`realTeamNumber` = CASE `mt`.`realTeamSide`
                                                  WHEN 'Home' THEN 1
                                                  WHEN 'Away' THEN 2
                                                  ELSE NULL
                                               END
                   WHERE `m`.`realCompetitionID` = :realCompetitionID
            """,
                {"realCompetitionID": real_competition_id},
            )

            # Query #4: Insert new RealTeams to RealTeamMembers
            SyncRealService._exec(
                db,
                task,
                "to_RealTeamMembers(ins)",
                """
                INSERT INTO `RealTeamMembers`
                    (`realTeamMemberKey`, `prevRealTeamMemberKey`, `nextRealTeamMemberKey`,
                     `baseRealCompetitionID`, `extraRealCompetitionID`,
                     `isTeam`, `isPlayer`,
                     `realTeamID`, `realTeamUID`, `realTeamName`, `realTeamShortName`,
                     `realPlayerID`, `realPlayerUID`, `firstName`, `lastName`, `knownName`,
                     `name`, `sortName`,
                     `position`, `draftPosition`, `draftPositionOrder`,
                     `birthDate`, `weight`, `height`, `jerseyNumber`,
                     `enabled`,
                     `last_ranking`, `last_timePlayed`, `last_gamePlayed`, `last_goals`, `last_assists`,
                     `last_goalsConceded`, `last_yellowCards`, `last_redCards`, `last_cleanSheet`,
                     `last_played`, `last_won`, `last_draw`, `last_lost`, `last_goalsFor`, `last_goalsAgainst`, `last_pointsL1`,
                     `ranking`,
                     `timePlayed`, `gamePlayed`, `goals`, `assists`, `goalsConceded`, `yellowCards`, `redCards`, `cleanSheet`,
                     `played`, `won`, `draw`, `lost`, `goalsFor`, `goalsAgainst`, `pointsL1`, `livePointsL1`,
                     `lastF7Date`, `lastF42Date`, `lastFDate`,
                     `createdIn`, `updatedIn`)
                SELECT `t`.`realTeamMemberKey`,
                       IF(`t`.`prevRealTeamID` IS null, null, CONCAT('T', `t`.`prevRealTeamID`)),
                       IF(`t`.`nextRealTeamID` IS null, null, CONCAT('T', `t`.`nextRealTeamID`)),
                       `t`.`baseRealCompetitionID`, `t`.`extraRealCompetitionID`,
                       1, 0,
                       `t`.`realTeamID`, `t`.`realTeamUID`, `t`.`realTeamName`, `t`.`realTeamShortName`,
                       null, null, null, null, null,
                       `t`.`realTeamName`, `t`.`realTeamName`,
                       :draftPosition, :draftPosition, :draftPositionOrder,
                       null, null, null, null,
                       1,
                       null, null, null, null, null, null, null, null, null,
                       null, null, null, null, null, null, 0,
                       `t`.`ranking`,
                       null, null, null, null, null, null, null, null,
                       0, 0, 0, 0, 0, 0, 0, 0,
                       `t`.`lastF7Date`, `t`.`lastF42Date`, `t`.`lastFDate`,
                       `t`.`createdIn`, `t`.`updatedIn`
                FROM `RealTeams` `t`
                LEFT OUTER JOIN `RealTeamMembers` `m` ON `m`.`realTeamMemberKey` = `t`.`realTeamMemberKey`
                WHERE `t`.`realTeamID` = `t`.`baseRealTeamID`
                  AND `m`.`realTeamMemberID` IS null
                  AND `t`.`realCompetitionID` = :realCompetitionID
            """,
                {
                    "realCompetitionID": real_competition_id,
                    "draftPosition": _dp,
                    "draftPositionOrder": _dp_order,
                },
            )

            # Query #5: Update realTeamMemberID
            SyncRealService._exec(
                db,
                task,
                "from_realTeamMemberID(upd)",
                """
                UPDATE `RealTeams` `t`
                   LEFT OUTER JOIN `RealTeamMembers` `m` ON `m`.`realTeamMemberKey` = CONCAT('T', `t`.`baseRealTeamID`)
                   SET `t`.`realTeamMemberID` = `m`.`realTeamMemberID`
                   WHERE `t`.`realCompetitionID` = :realCompetitionID
            """,
                {"realCompetitionID": real_competition_id},
            )

            # Query #6: Update old RealTeams to RealTeamMembers
            SyncRealService._exec(
                db,
                task,
                "to_RealTeamMembers(upd)",
                """
                UPDATE `RealTeamMembers` `m`
                   INNER JOIN `RealTeams` `t` ON `m`.`realTeamMemberKey` = `t`.`realTeamMemberKey`
                   SET `m`.`realTeamMemberID` = `t`.`realTeamMemberID`,
                       `m`.`realTeamMemberKey` = `t`.`realTeamMemberKey`,
                       `m`.`prevRealTeamMemberKey` = IF(`t`.`prevRealTeamID` IS null, null, CONCAT('T', `t`.`prevRealTeamID`)),
                       `m`.`nextRealTeamMemberKey` = IF(`t`.`nextRealTeamID` IS null, null, CONCAT('T', `t`.`nextRealTeamID`)),
                       `m`.`baseRealCompetitionID` = `t`.`baseRealCompetitionID`,
                       `m`.`extraRealCompetitionID` = `t`.`extraRealCompetitionID`,
                       `m`.`isTeam` = 1,
                       `m`.`isPlayer` = 0,
                       `m`.`realTeamID` = `t`.`realTeamID`,
                       `m`.`realTeamUID` = `t`.`realTeamUID`,
                       `m`.`realTeamName` = `t`.`realTeamName`,
                       `m`.`realTeamShortName` = `t`.`realTeamShortName`,
                       `m`.`realPlayerID` = null,
                       `m`.`realPlayerUID` = null,
                       `m`.`firstName` = null,
                       `m`.`lastName` = null,
                       `m`.`knownName` = null,
                       `m`.`name` = `t`.`realTeamName`,
                       `m`.`sortName` = `t`.`realTeamName`,
                       `m`.`position` = :draftPosition,
                       `m`.`draftPosition` = :draftPosition,
                       `m`.`draftPositionOrder` = :draftPositionOrder,
                       `m`.`birthDate` = null,
                       `m`.`weight` = null,
                       `m`.`height` = null,
                       `m`.`jerseyNumber` = null,
                       `m`.`last_ranking` = null,
                       `m`.`last_timePlayed` = null,
                       `m`.`last_gamePlayed` = null,
                       `m`.`last_goals` = null,
                       `m`.`last_assists` = null,
                       `m`.`last_goalsConceded` = null,
                       `m`.`last_yellowCards` = null,
                       `m`.`last_redCards` = null,
                       `m`.`last_cleanSheet` = null,
                       `m`.`timePlayed` = null,
                       `m`.`gamePlayed` = null,
                       `m`.`goals` = null,
                       `m`.`assists` = null,
                       `m`.`goalsConceded` = null,
                       `m`.`yellowCards` = null,
                       `m`.`redCards` = null,
                       `m`.`cleanSheet` = null,
                       `m`.`lastF7Date` = `t`.`lastF7Date`,
                       `m`.`lastF42Date` = `t`.`lastF42Date`,
                       `m`.`lastFDate` = `t`.`lastFDate`,
                       `m`.`createdIn` = `t`.`createdIn`,
                       `m`.`updatedIn` = `t`.`updatedIn`
                   WHERE `t`.`realTeamID` = `t`.`baseRealTeamID`
                     AND `t`.`realCompetitionID` = :realCompetitionID
            """,
                {
                    "realCompetitionID": real_competition_id,
                    "draftPosition": _dp,
                    "draftPositionOrder": _dp_order,
                },
            )

        except Exception as e:
            task.add_error(str(e))

        task.close(status=Task.COMPLETED if not task.errors else Task.ERROR)
        return task

    @staticmethod
    def _sync_real_players(db: Session, real_competition_id: int) -> Task:
        """Sync RealPlayers and the player rows in RealTeamMembers.

        Runs six queries in order:
          1. Set baseRealPlayerID and realTeamMemberKey on RealPlayers.
          2. Propagate competition and team fields from RealTeams into RealPlayers.
          3. Set prevRealPlayerID / nextRealPlayerID on RealPlayers (cross-season links).
          4. Insert new RealPlayers rows into RealTeamMembers (base-season outfield players only).
          5. Write realTeamMemberID back from RealTeamMembers into RealPlayers.
          6. Update existing RealTeamMembers rows with current RealPlayers data.

        Args:
            db: Database session.
            real_competition_id: RealCompetitionID to sync.

        Returns:
            Task with queries_executed and rows_affected counts.
        """
        task = Task(
            name="_sync_real_players", status=Task.RUNNING, status_on_error=Task.ERROR
        )
        task.init_info("queries_executed", "rows_affected", default=0)

        try:
            # Query #1: Set base fields
            SyncRealService._exec(
                db,
                task,
                "base_fields(upd)",
                """
                UPDATE `RealPlayers` `p`
                   LEFT OUTER JOIN `RealPlayers` `p1`
                      ON `p`.`baseRealCompetitionID` = `p1`.`realCompetitionID`
                      AND `p`.`realPlayerUID` = `p1`.`realPlayerUID`
                   SET `p`.`baseRealPlayerID` = `p1`.`realPlayerID`,
                       `p`.`realTeamMemberKey` = CONCAT('P', `p1`.`realPlayerID`)
                   WHERE `p`.`realCompetitionID` = :realCompetitionID
            """,
                {"realCompetitionID": real_competition_id},
            )

            # Query #2: Sync from RealTeams
            SyncRealService._exec(
                db,
                task,
                "from_RealTeams(upd)",
                """
                UPDATE `RealPlayers` `p`
                   LEFT OUTER JOIN `RealTeams` `t` ON `t`.`realTeamID` = `p`.`realTeamID`
                   SET `p`.`realCompetitionID` = `t`.`realCompetitionID`,
                       `p`.`realCompetitionUID` = `t`.`realCompetitionUID`,
                       `p`.`realCompetitionSYMID` = `t`.`realCompetitionSYMID`,
                       `p`.`realCompetitionSeasonId` = `t`.`realCompetitionSeasonId`,
                       `p`.`baseRealCompetitionID` = `t`.`baseRealCompetitionID`,
                       `p`.`extraRealCompetitionID` = `t`.`extraRealCompetitionID`,
                       `p`.`realTeamUID` = `t`.`realTeamUID`,
                       `p`.`baseRealTeamID` = `t`.`baseRealTeamID`,
                       `p`.`baseRealTeamUID` = `t`.`baseRealTeamUID`,
                       `p`.`baseRealTeamName` = `t`.`baseRealTeamName`,
                       `p`.`baseRealTeamShortName` = `t`.`baseRealTeamShortName`
                   WHERE `p`.`realCompetitionID` = :realCompetitionID
            """,
                {"realCompetitionID": real_competition_id},
            )

            # Query #3: Update prev and next
            SyncRealService._exec(
                db,
                task,
                "prev_and_next(upd)",
                """
                UPDATE `RealPlayers` `p`
                   LEFT OUTER JOIN `RealCompetitions` `c` ON `p`.`realCompetitionID` = `c`.`realCompetitionID`
                   LEFT OUTER JOIN `RealPlayers` `p_p`
                      ON `p_p`.`realCompetitionID` = `c`.`prevRealCompetitionID`
                      AND `p_p`.`realPlayerUID` = `p`.`realPlayerUID`
                   LEFT OUTER JOIN `RealPlayers` `p_n`
                      ON `p_n`.`realCompetitionID` = `c`.`nextRealCompetitionID`
                      AND `p_n`.`realPlayerUID` = `p`.`realPlayerUID`
                   SET `p`.`prevRealPlayerID` = `p_p`.`realPlayerID`,
                       `p`.`nextRealPlayerID` = `p_n`.`realPlayerID`
                   WHERE `p`.`realCompetitionID` = :realCompetitionID
            """,
                {"realCompetitionID": real_competition_id},
            )

            # Query #4: Insert new RealPlayers to RealTeamMembers
            SyncRealService._exec(
                db,
                task,
                "to_RealTeamMembers(ins)",
                """
                INSERT INTO `RealTeamMembers`
                    (`realTeamMemberKey`, `prevRealTeamMemberKey`, `nextRealTeamMemberKey`,
                     `baseRealCompetitionID`, `extraRealCompetitionID`,
                     `isTeam`, `isPlayer`,
                     `realTeamID`, `realTeamUID`, `realTeamName`, `realTeamShortName`,
                     `realPlayerID`, `realPlayerUID`, `firstName`, `lastName`, `knownName`,
                     `name`, `sortName`,
                     `position`, `draftPosition`, `draftPositionOrder`,
                     `birthDate`, `weight`, `height`, `jerseyNumber`,
                     `enabled`,
                     `last_ranking`, `last_timePlayed`, `last_gamePlayed`, `last_goals`, `last_assists`,
                     `last_goalsConceded`, `last_yellowCards`, `last_redCards`, `last_cleanSheet`,
                     `last_played`, `last_won`, `last_draw`, `last_lost`, `last_goalsFor`, `last_goalsAgainst`, `last_pointsL1`,
                     `ranking`,
                     `timePlayed`, `gamePlayed`, `goals`, `assists`, `goalsConceded`, `yellowCards`, `redCards`, `cleanSheet`,
                     `played`, `won`, `draw`, `lost`, `goalsFor`, `goalsAgainst`, `pointsL1`, `livePointsL1`,
                     `lastF7Date`, `lastF42Date`, `lastFDate`,
                     `createdIn`, `updatedIn`)
                SELECT `p`.`realTeamMemberKey`,
                       IF(`p`.`prevRealPlayerID` IS null, null, CONCAT('P', `p`.`prevRealPlayerID`)),
                       IF(`p`.`nextRealPlayerID` IS null, null, CONCAT('P', `p`.`nextRealPlayerID`)),
                       `p`.`baseRealCompetitionID`, `p`.`extraRealCompetitionID`,
                       0, 1,
                       `p`.`realTeamID`, `p`.`realTeamUID`, `p`.`baseRealTeamName`, `p`.`baseRealTeamShortName`,
                       `p`.`realPlayerID`, `p`.`realPlayerUID`, `p`.`firstName`, `p`.`lastName`, `p`.`knownName`,
                       IFNULL(`p`.`knownName`, CONCAT(`p`.`firstName`, ' ', `p`.`lastName`)),
                       IFNULL(`p`.`knownName`, CONCAT(`p`.`lastName`, ' ', `p`.`firstName`)),
                       `p`.`position`, `p`.`draftPosition`, `p`.`draftPositionOrder`,
                       `p`.`birthDate`, `p`.`weight`, `p`.`height`, `p`.`jerseyNumber`,
                       1,
                       null, 0, 0, 0, 0, 0, 0, 0, 0,
                       null, null, null, null, null, null, 0,
                       `p`.`ranking`,
                       0, 0, 0, 0, 0, 0, 0, 0,
                       null, null, null, null, null, null, 0, 0,
                       `p`.`lastF7Date`, `p`.`lastF42Date`, `p`.`lastFDate`,
                       `p`.`createdIn`, `p`.`updatedIn`
                FROM `RealPlayers` `p`
                LEFT OUTER JOIN `RealTeamMembers` `m` ON `m`.`realTeamMemberKey` = `p`.`realTeamMemberKey`
                WHERE `p`.`realPlayerID` = `p`.`baseRealPlayerID`
                  AND `m`.`realTeamMemberID` IS null
                  AND `p`.`draftPosition` IN (:dp_1, :dp_2, :dp_3, :dp_4)
                  AND `p`.`realCompetitionID` = :realCompetitionID
            """,
                {
                    "realCompetitionID": real_competition_id,
                    "dp_1": DraftPositionConstants.GOALKEEPER,
                    "dp_2": DraftPositionConstants.DEFENDER,
                    "dp_3": DraftPositionConstants.MIDFIELDER,
                    "dp_4": DraftPositionConstants.STRIKER,
                },
            )

            # Query #5: Update realTeamMemberID
            SyncRealService._exec(
                db,
                task,
                "from_realTeamMemberID(upd)",
                """
                UPDATE `RealPlayers` `p`
                   LEFT OUTER JOIN `RealTeamMembers` `m` ON `m`.`realTeamMemberKey` = CONCAT('P', `p`.`baseRealPlayerID`)
                   SET `p`.`realTeamMemberID` = `m`.`realTeamMemberID`
                   WHERE `p`.`realCompetitionID` = :realCompetitionID
            """,
                {"realCompetitionID": real_competition_id},
            )

            # Query #6: Update old RealPlayers to RealTeamMembers
            SyncRealService._exec(
                db,
                task,
                "from_RealTeamMembers(upd)",
                """
                UPDATE `RealTeamMembers` `m`
                   INNER JOIN `RealPlayers` `p` ON `m`.`realTeamMemberKey` = `p`.`realTeamMemberKey`
                   SET `m`.`realTeamMemberID` = `p`.`realTeamMemberID`,
                       `m`.`realTeamMemberKey` = `p`.`realTeamMemberKey`,
                       `m`.`prevRealTeamMemberKey` = IF(`p`.`prevRealPlayerID` IS null, null, CONCAT('P', `p`.`prevRealPlayerID`)),
                       `m`.`nextRealTeamMemberKey` = IF(`p`.`nextRealPlayerID` IS null, null, CONCAT('P', `p`.`nextRealPlayerID`)),
                       `m`.`baseRealCompetitionID` = `p`.`baseRealCompetitionID`,
                       `m`.`extraRealCompetitionID` = `p`.`extraRealCompetitionID`,
                       `m`.`isTeam` = 0,
                       `m`.`isPlayer` = 1,
                       `m`.`realTeamID` = `p`.`realTeamID`,
                       `m`.`realTeamUID` = `p`.`realTeamUID`,
                       `m`.`realTeamName` = `p`.`baseRealTeamName`,
                       `m`.`realTeamShortName` = `p`.`baseRealTeamShortName`,
                       `m`.`realPlayerID` = `p`.`realPlayerID`,
                       `m`.`realPlayerUID` = `p`.`realPlayerUID`,
                       `m`.`firstName` = `p`.`firstName`,
                       `m`.`lastName` = `p`.`lastName`,
                       `m`.`knownName` = `p`.`knownName`,
                       `m`.`name` = IFNULL(`p`.`knownName`, CONCAT(`p`.`firstName`, ' ', `p`.`lastName`)),
                       `m`.`sortName` = IFNULL(`p`.`knownName`, CONCAT(`p`.`lastName`, ' ', `p`.`firstName`)),
                       `m`.`position` = IF(`m`.`draftPosition` IS null, `p`.`position`, `m`.`position`),
                       `m`.`draftPosition` = IF(`m`.`draftPosition` IS null, `p`.`draftPosition`, `m`.`draftPosition`),
                       `m`.`draftPositionOrder` = IF(`m`.`draftPosition` IS null, `p`.`draftPositionOrder`, `m`.`draftPositionOrder`),
                       `m`.`birthDate` = `p`.`birthDate`,
                       `m`.`weight` = `p`.`weight`,
                       `m`.`height` = `p`.`height`,
                       `m`.`jerseyNumber` = `p`.`jerseyNumber`,
                       `m`.`last_played` = null,
                       `m`.`last_won` = null,
                       `m`.`last_draw` = null,
                       `m`.`last_lost` = null,
                       `m`.`last_goalsFor` = null,
                       `m`.`last_goalsAgainst` = null,
                       `m`.`played` = null,
                       `m`.`won` = null,
                       `m`.`draw` = null,
                       `m`.`lost` = null,
                       `m`.`goalsFor` = null,
                       `m`.`goalsAgainst` = null,
                       `m`.`lastF7Date` = `p`.`lastF7Date`,
                       `m`.`lastF42Date` = `p`.`lastF42Date`,
                       `m`.`lastFDate` = `p`.`lastFDate`,
                       `m`.`createdIn` = `p`.`createdIn`,
                       `m`.`updatedIn` = `p`.`updatedIn`
                   WHERE `p`.`realPlayerID` = `p`.`baseRealPlayerID`
                     AND `p`.`realCompetitionID` = :realCompetitionID
            """,
                {"realCompetitionID": real_competition_id},
            )

        except Exception as e:
            task.add_error(str(e))

        task.close(status=Task.COMPLETED if not task.errors else Task.ERROR)
        return task

    @staticmethod
    def _sync_real_team_members(db: Session, real_competition_id: int) -> Task:
        """Calculate and write per-match-day RealStandings rows from RealTeamMembers data.

        For each competition in scope (base, and optionally extra when the base uses it),
        iterates over existing RealStandings rows ordered by match day, accumulates stats
        per member via _calc_rtm, then INSERTs or UPDATEs RealStandings at the end of
        each match day. Place and ranking fields are calculated by _sort_members before
        each save.

        Args:
            db: Database session.
            real_competition_id: RealCompetitionID to sync (base or extra).

        Returns:
            Task with per-competition insert/update counts.
        """
        task = Task(
            name="_sync_real_team_members",
            status=Task.RUNNING,
            status_on_error=Task.ERROR,
        )
        from app.services import QueryService

        task.init_info("queries_executed", "rows_affected", default=0)

        try:
            # Load base and extra competitions
            base_comp: dict | None = QueryService.get_base_competition(
                db, real_competition_id
            )
            extra_comp: dict | None = QueryService.get_extra_competition(
                db, real_competition_id
            )

            if not base_comp or not extra_comp:
                task.add_error("No RealCompetitions found for given ID")
                task.close(status=Task.ERROR)
                return task

            # Load members and build the competition list (base always included; extra only when configured)
            sql_cache = {}
            match_teams = {}
            members = SyncRealService._read_real_team_members(db, base_comp)
            comp_list = [base_comp]
            if (
                base_comp["useExtraRealCompetition"]
                and base_comp["realCompetitionExtraMatchDay"]
            ):
                comp_list.append(extra_comp)

            for comp in comp_list:
                task.init_info(
                    f"{comp['realCompetitionSYMID']}(ins)",
                    f"{comp['realCompetitionSYMID']}(upd)",
                    default=0,
                )
                match_day: int | None = None
                for row in SyncRealService._read_real_standings(db, comp):
                    if match_day != row["realCompetitionMatchDay"]:
                        SyncRealService._save_members(
                            db, members, comp, match_teams, match_day, sql_cache, task
                        )
                        match_day = row["realCompetitionMatchDay"]
                        match_teams = SyncRealService._read_real_match_teams(
                            db, comp, match_day
                        )
                    key = row["realTeamMemberKey"]
                    if key in members:
                        members[key] = SyncRealService._calc_rtm(
                            members[key], match_teams, row
                        )
                SyncRealService._save_members(
                    db, members, comp, match_teams, match_day, sql_cache, task
                )

        except Exception as e:
            task.add_error(str(e))

        task.close(status=Task.COMPLETED if not task.errors else Task.ERROR)
        return task

    @staticmethod
    def _sync_real_standings(db: Session, real_competition_id: int) -> Task:
        """Copy final-matchday RealStandings stats back into RealTeamMembers.

        Runs two UPDATE queries:
          1. last_* fields: joined on prevRealTeamMemberKey to pull previous-season stats.
          2. Current-season fields: joined on realTeamMemberKey to pull this season's stats.
        Both queries filter to the last match day of each competition.

        Args:
            db: Database session.
            real_competition_id: RealCompetitionID to sync (used to resolve the base competition).

        Returns:
            Task with queries_executed and rows_affected counts.
        """
        task = Task(
            name="_sync_real_standings", status=Task.RUNNING, status_on_error=Task.ERROR
        )
        task.init_info("queries_executed", "rows_affected", default=0)

        try:
            from app.services import QueryService

            base_comp_id = QueryService.get_base_competition_id(db, real_competition_id)
            # Query #1: Copy last-season stats from RealStandings into RealTeamMembers
            SyncRealService._exec(
                db,
                task,
                "to_RealTeamMembers-last(upd)",
                """
                UPDATE `RealTeamMembers` `rtm`
                   LEFT OUTER JOIN `RealStandings` `rs`
                      ON `rs`.`realTeamMemberKey` = `rtm`.`prevRealTeamMemberKey`
                      AND `rs`.`realCompetitionMatchDay` = `rs`.`realCompetitionLastMatchDay`
                      AND `rs`.`realCompetitionID` = `rs`.`baseRealCompetitionID`
                   SET `rtm`.`last_ranking` = `rs`.`ranking`,
                       `rtm`.`last_timePlayed` = `rs`.`timePlayed`,
                       `rtm`.`last_gamePlayed` = `rs`.`gamePlayed`,
                       `rtm`.`last_goals` = `rs`.`goals`,
                       `rtm`.`last_assists` = `rs`.`assists`,
                       `rtm`.`last_goalsConceded` = `rs`.`goalsConceded`,
                       `rtm`.`last_yellowCards` = `rs`.`yellowCards`,
                       `rtm`.`last_redCards` = `rs`.`redCards`,
                       `rtm`.`last_cleanSheet` = `rs`.`cleanSheet`,
                       `rtm`.`last_played` = `rs`.`played`,
                       `rtm`.`last_won` = `rs`.`won`,
                       `rtm`.`last_draw` = `rs`.`draw`,
                       `rtm`.`last_lost` = `rs`.`lost`,
                       `rtm`.`last_goalsFor` = `rs`.`goalsFor`,
                       `rtm`.`last_goalsAgainst` = `rs`.`goalsAgainst`,
                       `rtm`.`last_pointsL1` = `rs`.`pointsL1`
                   WHERE `rtm`.`baseRealCompetitionID` = :baseRealCompetitionID
            """,
                {"baseRealCompetitionID": base_comp_id},
            )

            # Query #2: Copy current-season stats from RealStandings into RealTeamMembers
            SyncRealService._exec(
                db,
                task,
                "to_RealTeamMembers-curr(upd)",
                """
                UPDATE `RealTeamMembers` `rtm`
                   LEFT OUTER JOIN `RealStandings` `rs`
                      ON `rs`.`realTeamMemberKey` = `rtm`.`realTeamMemberKey`
                      AND `rs`.`realCompetitionMatchDay` = `rs`.`realCompetitionLastMatchDay`
                      AND `rs`.`realCompetitionID` = `rs`.`baseRealCompetitionID`
                   SET `rtm`.`ranking` = `rs`.`ranking`,
                       `rtm`.`timePlayed` = `rs`.`timePlayed`,
                       `rtm`.`gamePlayed` = `rs`.`gamePlayed`,
                       `rtm`.`goals` = `rs`.`goals`,
                       `rtm`.`assists` = `rs`.`assists`,
                       `rtm`.`goalsConceded` = `rs`.`goalsConceded`,
                       `rtm`.`yellowCards` = `rs`.`yellowCards`,
                       `rtm`.`redCards` = `rs`.`redCards`,
                       `rtm`.`cleanSheet` = `rs`.`cleanSheet`,
                       `rtm`.`played` = `rs`.`played`,
                       `rtm`.`won` = `rs`.`won`,
                       `rtm`.`draw` = `rs`.`draw`,
                       `rtm`.`lost` = `rs`.`lost`,
                       `rtm`.`goalsFor` = `rs`.`goalsFor`,
                       `rtm`.`goalsAgainst` = `rs`.`goalsAgainst`,
                       `rtm`.`pointsL1` = `rs`.`pointsL1`,
                       `rtm`.`livePointsL1` = `rs`.`livePointsL1`
                   WHERE `rtm`.`baseRealCompetitionID` = :baseRealCompetitionID
            """,
                {"baseRealCompetitionID": base_comp_id},
            )

        except Exception as e:
            task.add_error(str(e))

        task.close(status=Task.COMPLETED if not task.errors else Task.ERROR)
        return task

    @staticmethod
    def _save_members(
        db: Session,
        members: dict,
        comp: dict,
        match_teams: dict,
        match_day: int | None,
        sql_cache: dict,
        task: Task,
    ) -> None:
        """Sort members, then INSERT or UPDATE their RealStandings row for this match day.

        Skips the entire save when match_day is None (no rows seen yet). SQL is built
        once per command type (ins/upd) via sql_cache and reused for all members.
        After saving, _clean_members resets per-match-day accumulated fields.

        Args:
            db: Database session.
            members: Dict of member dicts keyed by realTeamMemberKey.
            comp: Competition dict used to fill competition columns in the row.
            match_teams: Dict keyed by realTeamID with match result data.
            match_day: Current match day number, or None if no rows have been processed.
            sql_cache: Mutable cache dict; keys ``"ins"`` and ``"upd"`` store built SQL.
            task: Task whose per-competition insert/update counters are incremented.
        """
        if match_day is None:
            return
        SyncRealService._sort_members(members)
        for member in members.values():
            values = SyncRealService._get_rtm_values(
                member, comp, match_teams, match_day
            )
            if "realStandingID" not in values:
                cmd = "ins"
                if cmd not in sql_cache:
                    sql_cache[cmd] = sql_insert("RealStandings", values)
            else:
                cmd = "upd"
                if cmd not in sql_cache:
                    sql_cache[cmd] = sql_update(
                        "RealStandings", values, id_name="realStandingID"
                    )
            db.execute(text(sql_cache[cmd]), values)
            task.inc(f"{comp['realCompetitionSYMID']}({cmd})")
        SyncRealService._clean_members(members)

    @staticmethod
    def _get_rtm_values(
        member: dict, comp: dict, match_teams: dict, match_day: int
    ) -> dict:
        """Build the full column dict for one RealStandings INSERT or UPDATE.

        Player-only fields (timePlayed, goals, points breakdowns, etc.) are set to
        None for team members, and team-only fields (played, won/draw/lost, place, etc.)
        are set to None for player members. realStandingID is included only when the
        member already has one (UPDATE path); omitting it triggers the INSERT path in
        _save_members. createdIn is added only on INSERT; updatedIn is always set.

        Args:
            member: Accumulated member dict (from _read_real_team_members + _calc_rtm).
            comp: Competition dict supplying competition-level columns.
            match_teams: Dict keyed by realTeamID with match result and score data.
            match_day: Match day number being saved.

        Returns:
            dict mapping column name → value, ready to pass as SQLAlchemy bind params.
        """
        t_1 = member["realTeamID"]
        t_2 = match_teams[t_1]["oppositeRealTeamID"]
        if "realStandingID" not in member:
            values = {}
        else:
            values = {"realStandingID": member["realStandingID"]}
        values["realTeamMemberID"] = member["realTeamMemberID"]
        values["realTeamMemberKey"] = member["realTeamMemberKey"]
        values["prevRealTeamMemberKey"] = member["prevRealTeamMemberKey"]
        values["nextRealTeamMemberKey"] = member["nextRealTeamMemberKey"]
        values["realCompetitionID"] = comp["realCompetitionID"]
        values["realCompetitionUID"] = comp["realCompetitionUID"]
        values["realCompetitionSYMID"] = comp["realCompetitionSYMID"]
        values["realCompetitionSeasonId"] = comp["realCompetitionSeasonId"]
        values["realCompetitionMatchDay"] = match_day
        values["realCompetitionLastMatchDay"] = comp["realCompetitionLastMatchDay"]
        values["baseRealCompetitionID"] = comp["baseRealCompetitionID"]
        values["extraRealCompetitionID"] = comp["extraRealCompetitionID"]
        values["isTeam"] = member["isTeam"]
        values["isPlayer"] = member["isPlayer"]
        values["baseMatchDay"] = match_day
        values["realMatchID"] = match_teams[t_1]["realMatchID"]
        values["realMatchTeamID"] = match_teams[t_1]["realMatchTeamID"]
        values["realMatchDate"] = match_teams[t_1]["realMatchDate"]
        values["realMatchTime"] = match_teams[t_1]["realMatchTime"]
        values["realMatchStatus"] = match_teams[t_1]["realMatchStatus"]
        values["realTeamID"] = match_teams[t_1]["realTeamID"]
        values["realTeamUID"] = match_teams[t_1]["realTeamUID"]
        values["realTeamName"] = match_teams[t_1]["realTeamName"]
        values["realTeamShortName"] = match_teams[t_1]["realTeamShortName"]
        values["realTeamScore"] = match_teams[t_1]["realTeamScore"]
        values["realTeamSide"] = match_teams[t_1]["realTeamSide"]
        values["oppositeRealTeamID"] = match_teams[t_2]["realTeamID"]
        values["oppositeRealTeamUID"] = match_teams[t_2]["realTeamUID"]
        values["oppositeRealTeamName"] = match_teams[t_2]["realTeamName"]
        values["oppositeRealTeamShortName"] = match_teams[t_2]["realTeamShortName"]
        values["oppositeRealTeamScore"] = match_teams[t_2]["realTeamScore"]
        if member["isTeam"]:
            values["realPlayerID"] = None
            values["realPlayerUID"] = None
            values["firstName"] = None
            values["lastName"] = None
            values["knownName"] = None
        else:
            values["realPlayerID"] = member["realPlayerID"]
            values["realPlayerUID"] = member["realPlayerUID"]
            values["firstName"] = member["firstName"]
            values["lastName"] = member["lastName"]
            values["knownName"] = member["knownName"]
        values["name"] = member["name"]
        values["sortName"] = member["sortName"]
        values["position"] = member["position"]
        values["draftPosition"] = member["draftPosition"]
        values["draftPositionOrder"] = member["draftPositionOrder"]
        if member["isTeam"]:
            values["timePlayed"] = None
            values["gamePlayed"] = None
            values["goals"] = None
            values["assists"] = None
            values["yellowCards"] = None
            values["redCards"] = None
            values["goalsConceded"] = None
            values["cleanSheet"] = None
            values["matchTimePlayed"] = None
            values["matchGamePlayed"] = None
            values["matchGoals"] = None
            values["matchAssists"] = None
            values["matchYellowCards"] = None
            values["matchRedCards"] = None
            values["matchGoalsConceded"] = None
            values["matchCleanSheet"] = None
            values["matchDayPlayed"] = None
        else:
            values["timePlayed"] = member["timePlayed"]
            values["gamePlayed"] = member["gamePlayed"]
            values["goals"] = member["goals"]
            values["assists"] = member["assists"]
            values["yellowCards"] = member["yellowCards"]
            values["redCards"] = member["redCards"]
            values["goalsConceded"] = member["goalsConceded"]
            values["cleanSheet"] = member["cleanSheet"]
            values["matchTimePlayed"] = member["matchTimePlayed"]
            values["matchGamePlayed"] = member["matchGamePlayed"]
            values["matchGoals"] = member["matchGoals"]
            values["matchAssists"] = member["matchAssists"]
            values["matchYellowCards"] = member["matchYellowCards"]
            values["matchRedCards"] = member["matchRedCards"]
            values["matchGoalsConceded"] = member["matchGoalsConceded"]
            values["matchCleanSheet"] = member["matchCleanSheet"]
            values["matchDayPlayed"] = member["matchDayPlayed"]
        if member["isTeam"]:
            values["matchWon"] = member["matchWon"]
            values["matchDraw"] = member["matchDraw"]
            values["matchLost"] = member["matchLost"]
            values["played"] = member["played"]
            values["won"] = member["won"]
            values["draw"] = member["draw"]
            values["lost"] = member["lost"]
            values["goalsFor"] = member["goalsFor"]
            values["goalsAgainst"] = member["goalsAgainst"]
            values["place"] = member["place"]
            values["playedHome"] = member["playedHome"]
            values["wonHome"] = member["wonHome"]
            values["drawHome"] = member["drawHome"]
            values["lostHome"] = member["lostHome"]
            values["goalsForHome"] = member["goalsForHome"]
            values["goalsAgainstHome"] = member["goalsAgainstHome"]
            values["placeHome"] = member["placeHome"]
            values["playedAway"] = member["playedAway"]
            values["wonAway"] = member["wonAway"]
            values["drawAway"] = member["drawAway"]
            values["lostAway"] = member["lostAway"]
            values["goalsForAway"] = member["goalsForAway"]
            values["goalsAgainstAway"] = member["goalsAgainstAway"]
            values["placeAway"] = member["placeAway"]
        else:
            values["matchWon"] = None
            values["matchDraw"] = None
            values["matchLost"] = None
            values["played"] = None
            values["won"] = None
            values["draw"] = None
            values["lost"] = None
            values["goalsFor"] = None
            values["goalsAgainst"] = None
            values["place"] = None
            values["playedHome"] = None
            values["wonHome"] = None
            values["drawHome"] = None
            values["lostHome"] = None
            values["goalsForHome"] = None
            values["goalsAgainstHome"] = None
            values["placeHome"] = None
            values["playedAway"] = None
            values["wonAway"] = None
            values["drawAway"] = None
            values["lostAway"] = None
            values["goalsForAway"] = None
            values["goalsAgainstAway"] = None
            values["placeAway"] = None
        if member["isTeam"]:
            values["matchPointsL1Played"] = None
            values["matchPointsL1GoalsAllowed"] = None
            values["matchPointsL1CleanSheet"] = None
            values["matchPointsL1Cards"] = None
            values["matchPointsL1Goals"] = None
            values["matchPointsL1Assists"] = None
            values["matchPointsL1OwnGoals"] = None
        else:
            values["matchPointsL1Played"] = member["matchPointsL1Played"]
            values["matchPointsL1GoalsAllowed"] = member["matchPointsL1GoalsAllowed"]
            values["matchPointsL1CleanSheet"] = member["matchPointsL1CleanSheet"]
            values["matchPointsL1Cards"] = member["matchPointsL1Cards"]
            values["matchPointsL1Goals"] = member["matchPointsL1Goals"]
            values["matchPointsL1Assists"] = member["matchPointsL1Assists"]
            values["matchPointsL1OwnGoals"] = member["matchPointsL1OwnGoals"]
        values["matchPointsL1"] = member["matchPointsL1"]
        if member["isTeam"]:
            values["pointsL1Played"] = None
            values["pointsL1GoalsAllowed"] = None
            values["pointsL1CleanSheet"] = None
            values["pointsL1Cards"] = None
            values["pointsL1Goals"] = None
            values["pointsL1Assists"] = None
            values["pointsL1OwnGoals"] = None
        else:
            values["pointsL1Played"] = member["pointsL1Played"]
            values["pointsL1GoalsAllowed"] = member["pointsL1GoalsAllowed"]
            values["pointsL1CleanSheet"] = member["pointsL1CleanSheet"]
            values["pointsL1Cards"] = member["pointsL1Cards"]
            values["pointsL1Goals"] = member["pointsL1Goals"]
            values["pointsL1Assists"] = member["pointsL1Assists"]
            values["pointsL1OwnGoals"] = member["pointsL1OwnGoals"]
        values["pointsL1"] = member["pointsL1"]
        values["livePointsL1"] = member["matchPointsL1"]
        values["ranking"] = member["ranking"]
        values["processed"] = 1
        if "realStandingID" not in member:
            values["createdIn"] = utc_now()
        values["updatedIn"] = utc_now()

        return values

    @staticmethod
    def _clean_members(members: dict) -> None:
        """Reset per-match-day fields on all members after a save.

        Drops realStandingID (so the next match day triggers an INSERT rather than UPDATE)
        and resets ranking/place fields to None so they are recalculated fresh.

        Args:
            members: Dict of member dicts keyed by realTeamMemberKey (modified in place).
        """
        for key in members:  # noqa: PLC0206
            members[key].pop("realStandingID", None)
            members[key]["ranking"] = None
            members[key]["place"] = None
            members[key]["placeHome"] = None
            members[key]["placeAway"] = None

    @staticmethod
    def _sort_members(members: dict) -> None:
        """Calculate and assign ranking, place, placeHome, and placeAway for all members.

        For each field, builds a sortable list via _get_sorting_data, sorts it using
        _compare (descending by points then goal difference then goals, ascending by name),
        and writes 1-based positions back into each member dict. Player members are
        excluded from place/placeHome/placeAway (only teams get league positions).

        Args:
            members: Dict of member dicts keyed by realTeamMemberKey (modified in place).
        """
        for field in ["ranking", "place", "placeHome", "placeAway"]:
            data = SyncRealService._get_sorting_data(members, field)
            data.sort(key=cmp_to_key(SyncRealService._compare))
            for i, item in enumerate(data):
                members[item["key"]][field] = i + 1

    @staticmethod
    def _compare(data_1: dict, data_2: dict) -> int:
        """Comparator for cmp_to_key sorting of member ranking/place data.

        Compares element-by-element through the ``values`` list (descending — higher is
        better), then falls back to ``name`` (ascending) for ties.

        Args:
            data_1: Dict with ``values`` (list of numerics) and ``name`` (str).
            data_2: Dict with the same structure.

        Returns:
            -1 if data_1 should rank higher, 1 if data_2 should, 0 if equal.
        """
        for i, value_1 in enumerate(data_1["values"]):
            value_2 = data_2["values"][i]
            if value_1 > value_2:
                return -1
            elif value_1 < value_2:
                return 1
        if data_1["name"] < data_2["name"]:
            return -1
        elif data_1["name"] > data_2["name"]:
            return 1
        return 0

    @staticmethod
    def _get_sorting_data(members: dict, field: str) -> list[dict]:
        """Build a sortable list of member entries for one ranking/place field.

        For ``ranking``: includes all members (teams and players), keyed on pointsL1.
        For ``place``/``placeHome``/``placeAway``: includes teams only; values are
        [pointsL1, goal_difference, goalsFor] for the relevant side.
        Player members are skipped for place fields (values=None → excluded).

        Args:
            members: Dict of member dicts keyed by realTeamMemberKey.
            field: One of ``"ranking"``, ``"place"``, ``"placeHome"``, ``"placeAway"``.

        Returns:
            List of dicts, each with ``key``, ``name``, and ``values``, ready for _compare.
        """
        data: list[dict] = []
        for member in members.values():
            if field == "ranking":
                values = [member["pointsL1"]]
            elif member["isTeam"]:
                side = field[-4:] if field[-4:] in ["Home", "Away"] else ""
                values = [
                    member["pointsL1"],
                    member["goalsFor" + side] - member["goalsAgainst" + side],
                    member["goalsFor" + side],
                ]
            else:
                values = None
            if values is not None:
                data.append(
                    {
                        "key": member["realTeamMemberKey"],
                        "name": member["sortName"],
                        "values": values,
                    }
                )
        return data

    @staticmethod
    def _calc_rtm(member: dict, match_teams: dict, stand: dict) -> dict:
        """Update a member's accumulated stats for one RealStandings row.

        Stamps realStandingID from the standing row, then delegates to
        _calc_rtm_team (for team members) or _calc_rtm_player (for player members).

        Args:
            member: Accumulated member dict to update (modified in place).
            match_teams: Dict keyed by realTeamID with match result data.
            stand: One RealStandings row dict (from _read_real_standings).

        Returns:
            The updated member dict (same object passed in).
        """
        member["realStandingID"] = stand["realStandingID"]
        if member["isTeam"]:
            return SyncRealService._calc_rtm_team(member, match_teams)
        else:
            return SyncRealService._calc_rtm_player(member, stand)

    @staticmethod
    def _calc_rtm_team(member: dict, match_teams: dict) -> dict:
        """Accumulate one match day's result into a team member's running totals.

        When the team's result is None (match not yet played or no score), only
        matchWon/matchDraw/matchLost are zeroed and no cumulative counts are touched.
        When played, updates played/won/draw/lost/goalsFor/goalsAgainst for both the
        overall side (``""``) and the specific side (``"Home"`` or ``"Away"``).

        Args:
            member: Accumulated team member dict to update (modified in place).
            match_teams: Dict keyed by realTeamID with realTeamPoints, realTeamScore,
                realTeamSide, realTeamResult, and oppositeRealTeamID.

        Returns:
            The updated member dict (same object passed in).
        """
        t_1 = member["realTeamID"]
        t_2 = match_teams[t_1]["oppositeRealTeamID"]
        if match_teams[t_1]["realTeamResult"] is None:
            member["matchWon"] = 0
            member["matchDraw"] = 0
            member["matchLost"] = 0
        else:
            member["matchWon"] = 1 if match_teams[t_1]["realTeamPoints"] == 3 else 0
            member["matchDraw"] = 1 if match_teams[t_1]["realTeamPoints"] == 1 else 0
            member["matchLost"] = 1 if match_teams[t_1]["realTeamPoints"] == 0 else 0
            side = match_teams[t_1]["realTeamSide"]
            for s in ["", side]:
                member["played" + s] += 1
                member["won" + s] += member["matchWon"]
                member["draw" + s] += member["matchDraw"]
                member["lost" + s] += member["matchLost"]
                member["goalsFor" + s] += match_teams[t_1]["realTeamScore"]
                member["goalsAgainst" + s] += match_teams[t_2]["realTeamScore"]
        member["matchPointsL1"] = match_teams[t_1]["realTeamPoints"]
        member["pointsL1"] += member["matchPointsL1"] or 0
        return member

    @staticmethod
    def _calc_rtm_player(member: dict, stand: dict) -> dict:
        """Accumulate one match day's stats into a player member's running totals.

        Copies all match* fields from the standing row onto the member (so the latest
        match values are always available for _get_rtm_values), then adds each to the
        corresponding cumulative field. matchPointsL1 is computed as the sum of all
        matchPointsL1* sub-components from the standing row.

        Args:
            member: Accumulated player member dict to update (modified in place).
            stand: One RealStandings row dict (from _read_real_standings).

        Returns:
            The updated member dict (same object passed in).
        """
        member["matchTimePlayed"] = stand["matchTimePlayed"]
        member["matchGamePlayed"] = stand["matchGamePlayed"]
        member["matchGoals"] = stand["matchGoals"]
        member["matchAssists"] = stand["matchAssists"]
        member["matchYellowCards"] = stand["matchYellowCards"]
        member["matchRedCards"] = stand["matchRedCards"]
        member["matchGoalsConceded"] = stand["matchGoalsConceded"]
        member["matchCleanSheet"] = stand["matchCleanSheet"]
        member["matchDayPlayed"] = stand["matchDayPlayed"]
        member["matchPointsL1Played"] = stand["matchPointsL1Played"]
        member["matchPointsL1GoalsAllowed"] = stand["matchPointsL1GoalsAllowed"]
        member["matchPointsL1CleanSheet"] = stand["matchPointsL1CleanSheet"]
        member["matchPointsL1Cards"] = stand["matchPointsL1Cards"]
        member["matchPointsL1Goals"] = stand["matchPointsL1Goals"]
        member["matchPointsL1Assists"] = stand["matchPointsL1Assists"]
        member["matchPointsL1OwnGoals"] = stand["matchPointsL1OwnGoals"]
        member["timePlayed"] += stand["matchTimePlayed"] or 0
        member["gamePlayed"] += stand["matchGamePlayed"] or 0
        member["goals"] += stand["matchGoals"] or 0
        member["assists"] += stand["matchAssists"] or 0
        member["yellowCards"] += stand["matchYellowCards"] or 0
        member["redCards"] += stand["matchRedCards"] or 0
        member["goalsConceded"] += stand["matchGoalsConceded"] or 0
        member["cleanSheet"] += stand["matchCleanSheet"] or 0

        # Aggregate points breakdown
        member["matchPointsL1"] = (
            (stand["matchPointsL1Played"] or 0)
            + (stand["matchPointsL1GoalsAllowed"] or 0)
            + (stand["matchPointsL1CleanSheet"] or 0)
            + (stand["matchPointsL1Cards"] or 0)
            + (stand["matchPointsL1Goals"] or 0)
            + (stand["matchPointsL1Assists"] or 0)
            + (stand["matchPointsL1OwnGoals"] or 0)
        )
        member["pointsL1Played"] += stand["matchPointsL1Played"] or 0
        member["pointsL1GoalsAllowed"] += stand["matchPointsL1GoalsAllowed"] or 0
        member["pointsL1CleanSheet"] += stand["matchPointsL1CleanSheet"] or 0
        member["pointsL1Cards"] += stand["matchPointsL1Cards"] or 0
        member["pointsL1Goals"] += stand["matchPointsL1Goals"] or 0
        member["pointsL1Assists"] += stand["matchPointsL1Assists"] or 0
        member["pointsL1OwnGoals"] += stand["matchPointsL1OwnGoals"] or 0
        member["pointsL1"] += member["matchPointsL1"]
        return member

    @staticmethod
    def _read_real_match_teams(db: Session, comp: dict, match_day: int) -> dict:
        """Load all RealMatchTeams rows for a competition and match day.

        Args:
            db: Database session.
            comp_id: RealCompetitionID to filter by.
            match_day: Match day number to filter by.

        Returns:
            dict keyed by realTeamID mapping to the row dict (match + match-team fields).
        """
        match_team_rows = db.execute(
            text("""
                 SELECT `m`.`realMatchID`,
                        `m`.`realMatchStatus`,
                        `m`.`realMatchDate`,
                        `m`.`realMatchTime`,
                        `m`.`realCompetitionID`,
                        `m`.`realCompetitionUID`,
                        `m`.`realCompetitionSYMID`,
                        `m`.`realCompetitionSeasonId`,
                        `m`.`realCompetitionMatchDay`,
                        `m`.`realCompetitionLastMatchDay`,
                        `m`.`baseRealCompetitionID`,
                        `m`.`extraRealCompetitionID`,
                        `mt`.`realMatchTeamID`,
                        `mt`.`realTeamMemberID`,
                        `mt`.`realTeamMemberKey`,
                        `mt`.`realTeamID`,
                        `mt`.`realTeamUID`,
                        `mt`.`realTeamName`,
                        `mt`.`realTeamShortName`,
                        `mt`.`realTeamScore`,
                        `mt`.`realTeamRealScore`,
                        `mt`.`realTeamSide`
                    FROM `RealMatchTeams` `mt`
                    INNER JOIN `RealMatches` `m` ON `m`.`realMatchID` = `mt`.`realMatchID`
                    WHERE `m`.`realCompetitionID` = :comp_id
                      AND `m`.`realCompetitionMatchDay` = :match_day
                      AND `mt`.`realTeamSide` IN ('Home', 'Away')
                 """),
            {
                "comp_id": comp["realCompetitionID"],
                "match_day": match_day,
            },
        ).fetchall()

        matches = {}
        match_teams = {}
        for row in match_team_rows:
            row_dict = (
                dict(row._mapping)
                if hasattr(row, "_mapping")
                else dict(zip(row.keys(), row))
            )
            match_teams[row_dict.get("realTeamID")] = row_dict
            if row_dict["realMatchID"] not in matches:
                matches[row_dict["realMatchID"]] = []
            matches[row_dict["realMatchID"]].append(row_dict["realTeamID"])

        return SyncRealService._calc_real_match_teams(match_teams, matches)

    @staticmethod
    def _calc_real_match_teams(match_teams: dict, matches: dict) -> dict:
        """Annotate each match-team row with oppositeRealTeamID, points, and result.

        For each match, identifies the two teams, links them as opposites, and computes
        realTeamPoints (3/1/0) and realTeamResult (1/0/-1) based on score comparison.
        When either score is None, both points and result are set to None.

        Args:
            match_teams: Dict keyed by realTeamID (modified in place).
            matches: Dict keyed by realMatchID mapping to a list of the two realTeamIDs.

        Returns:
            The updated match_teams dict (same object passed in).
        """
        for teams in matches.values():
            t_1, t_2 = teams
            match_teams[t_1]["oppositeRealTeamID"] = t_2
            match_teams[t_2]["oppositeRealTeamID"] = t_1
            score_1 = match_teams[t_1]["realTeamScore"]
            score_2 = match_teams[t_2]["realTeamScore"]
            if score_1 is None or score_2 is None:
                match_teams[t_1]["realTeamPoints"] = None
                match_teams[t_2]["realTeamPoints"] = None
                match_teams[t_1]["realTeamResult"] = None
                match_teams[t_2]["realTeamResult"] = None
            elif score_1 > score_2:
                match_teams[t_1]["realTeamPoints"] = 3
                match_teams[t_2]["realTeamPoints"] = 0
                match_teams[t_1]["realTeamResult"] = 1
                match_teams[t_2]["realTeamResult"] = -1
            elif score_1 < score_2:
                match_teams[t_1]["realTeamPoints"] = 0
                match_teams[t_2]["realTeamPoints"] = 3
                match_teams[t_1]["realTeamResult"] = -1
                match_teams[t_2]["realTeamResult"] = 1
            else:
                match_teams[t_1]["realTeamPoints"] = 1
                match_teams[t_2]["realTeamPoints"] = 1
                match_teams[t_1]["realTeamResult"] = 0
                match_teams[t_2]["realTeamResult"] = 0
        return match_teams

    @staticmethod
    def _read_real_team_members(db: Session, comp: dict) -> dict:
        """Load all team and player RealTeamMembers rows for a competition into a dict.

        Fetches teams (key prefix ``T``) and outfield players (key prefix ``P``,
        draftPosition in GK/DEF/MID/STR) for the given base/extra competition pair.
        Initialises all cumulative and match-day stat fields to 0 so _calc_rtm can
        safely use ``+=`` without checking for None. Also normalises draftPosition to
        the canonical constant value and recalculates draftPositionOrder.

        Args:
            db: Database session.
            comp: Base competition dict (must have baseRealCompetitionID and extraRealCompetitionID).

        Returns:
            Dict keyed by realTeamMemberKey mapping to the initialised member dict.
        """
        dp_g = DraftPositionConstants.GOALKEEPER
        dp_d = DraftPositionConstants.DEFENDER
        dp_m = DraftPositionConstants.MIDFIELDER
        dp_s = DraftPositionConstants.STRIKER
        dp_t = DraftPositionConstants.EPL_TEAM

        member_rows = db.execute(
            text("""
                 SELECT `realTeamMemberID`,
                        `realTeamMemberKey`,
                        `prevRealTeamMemberKey`,
                        `nextRealTeamMemberKey`,
                        IF(LEFT(`realTeamMemberKey`, 1) = 'T',1,0) AS `isTeam`,
                        IF(LEFT(`realTeamMemberKey`, 1) = 'P',1,0) AS `isPlayer`,
                        `realTeamID`,
                        `realTeamUID`,
                        `realTeamName`,
                        `realTeamShortName`,
                        `realPlayerID`,
                        `realPlayerUID`,
                        `firstName`,
                        `lastName`,
                        `knownName`,
                        `name`,
                        `sortName`,
                        `position`,
                        `draftPosition`,
                        `draftPositionOrder`
                FROM `RealTeamMembers`
                WHERE `baseRealCompetitionID` = :base_id
                  AND `extraRealCompetitionID` = :extra_id
                  AND ((LEFT(`realTeamMemberKey`, 1) = 'T') OR
                       ((LEFT(`realTeamMemberKey`, 1) = 'P') AND
                        (`draftPosition` IN (:dp_g, :dp_d, :dp_m, :dp_s))))
            """),
            {
                "base_id": comp["baseRealCompetitionID"],
                "extra_id": comp["extraRealCompetitionID"],
                "dp_g": dp_g,
                "dp_d": dp_d,
                "dp_m": dp_m,
                "dp_s": dp_s,
            },
        ).fetchall()

        members = {}
        for row in member_rows:
            member = (
                dict(row._mapping)
                if hasattr(row, "_mapping")
                else dict(zip(row.keys(), row))
            )
            if member["isTeam"]:
                member["realPlayerID"] = None
                member["realPlayerUID"] = None
                member["firstName"] = None
                member["lastName"] = None
                member["knownName"] = None
                member["draftPosition"] = dp_t
                member["pointsL1"] = 0
                member["matchPointsL1"] = 0
                member["matchWon"] = 0
                member["matchDraw"] = 0
                member["matchLost"] = 0
                for side in ["", "Home", "Away"]:
                    member["played" + side] = 0
                    member["won" + side] = 0
                    member["draw" + side] = 0
                    member["lost" + side] = 0
                    member["goalsFor" + side] = 0
                    member["goalsAgainst" + side] = 0
                    member["place" + side] = None
            else:
                member["timePlayed"] = 0
                member["gamePlayed"] = 0
                member["goals"] = 0
                member["assists"] = 0
                member["yellowCards"] = 0
                member["redCards"] = 0
                member["goalsConceded"] = 0
                member["cleanSheet"] = 0
                member["pointsL1Played"] = 0
                member["pointsL1GoalsAllowed"] = 0
                member["pointsL1CleanSheet"] = 0
                member["pointsL1Cards"] = 0
                member["pointsL1Goals"] = 0
                member["pointsL1Assists"] = 0
                member["pointsL1OwnGoals"] = 0
                member["pointsL1"] = 0
                member["matchTimePlayed"] = 0
                member["matchGamePlayed"] = 0
                member["matchGoals"] = 0
                member["matchAssists"] = 0
                member["matchYellowCards"] = 0
                member["matchRedCards"] = 0
                member["matchGoalsConceded"] = 0
                member["matchCleanSheet"] = 0
                member["matchDayPlayed"] = 0
                member["matchPointsL1Played"] = 0
                member["matchPointsL1GoalsAllowed"] = 0
                member["matchPointsL1CleanSheet"] = 0
                member["matchPointsL1Cards"] = 0
                member["matchPointsL1Goals"] = 0
                member["matchPointsL1Assists"] = 0
                member["matchPointsL1OwnGoals"] = 0
                member["matchPointsL1"] = 0
            if member["draftPosition"].upper() == dp_g.upper():
                member["draftPosition"] = dp_g
            elif member["draftPosition"].upper() == dp_d.upper():
                member["draftPosition"] = dp_d
            elif member["draftPosition"].upper() == dp_m.upper():
                member["draftPosition"] = dp_m
            elif member["draftPosition"].upper() == dp_s.upper():
                member["draftPosition"] = dp_s
            member["draftPositionOrder"] = DraftPositionConstants.get_order(
                member["draftPosition"]
            )

            members[member["realTeamMemberKey"]] = member

        return members

    @staticmethod
    def _read_real_standings(db: Session, rc: dict) -> Generator[dict, None, None]:
        """Yield each RealStandings row for the given competition, ordered by match day.

        Args:
            db: Database session.
            rc: Competition dict (from QueryService.get_competition). Filters rows
                to this competition and its first/last match day range.

        Yields:
            dict with keys: realStandingID, realTeamMemberKey,
            realCompetitionMatchDay, and all match* stat columns.
        """
        result = db.execute(
            text("""
                 SELECT `realStandingID`,
                        `realTeamMemberKey`,
                        `realCompetitionMatchDay`,
                        `matchTimePlayed`,
                        `matchGamePlayed`,
                        `matchGoals`,
                        `matchAssists`,
                        `matchYellowCards`,
                        `matchRedCards`,
                        `matchGoalsConceded`,
                        `matchCleanSheet`,
                        `matchDayPlayed`,
                        `matchPointsL1Played`,
                        `matchPointsL1GoalsAllowed`,
                        `matchPointsL1CleanSheet`,
                        `matchPointsL1Cards`,
                        `matchPointsL1Goals`,
                        `matchPointsL1Assists`,
                        `matchPointsL1OwnGoals`,
                        `matchPointsL1`
                    FROM `RealStandings`
                    WHERE `realCompetitionID` = :realCompetitionID
                      AND `realCompetitionMatchDay` >= :realCompetitionFirstMatchDay
                      AND `realCompetitionMatchDay` <= :realCompetitionLastMatchDay
                    ORDER BY `realCompetitionMatchDay`
            """),
            {
                "realCompetitionID": rc["realCompetitionID"],
                "realCompetitionFirstMatchDay": rc["realCompetitionFirstMatchDay"],
                "realCompetitionLastMatchDay": rc["realCompetitionLastMatchDay"],
            },
        )
        for row in result:
            yield (
                dict(row._mapping)
                if hasattr(row, "_mapping")
                else dict(zip(row.keys(), row))
            )

    @staticmethod
    def _exec(
        db: Session, task: Task, name: str, sql: str, params: dict | None = None
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
        task.inc("queries_executed")
        task.inc("rows_affected", task.assign(name, result.rowcount))
