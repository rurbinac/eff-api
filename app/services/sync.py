"""Data synchronization service for Real* tables.

Syncs redundant/denormalized data across tables to maintain consistency.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from app.constants import RealTeamMemberPositions, RealTeamTypes


class SyncService:
    """Synchronize application and Real* table data."""

    # Competition SYMIDs
    BASE_SYMID = 'EN_PR'
    EXTRA_SYMID = 'EN_FA'

    # Application-level syncs
    @staticmethod
    def _get_real_competition_id(db: Session) -> int:
        """Get realCompetitionID for current season (EN_PR)."""
        from app.services import QueryService
        current_season = QueryService.get_season_id()

        q = text("""
            SELECT realCompetitionID
            FROM `RealCompetitions`
            WHERE realCompetitionSeasonId = :season_id
              AND realCompetitionSYMID = :symid
            LIMIT 1
        """)
        result = db.execute(q, {
            'season_id': current_season,
            'symid': SyncService.BASE_SYMID,
        }).first()

        return result[0] if result else None

    @staticmethod
    def sync_fantasy(db: Session, real_competition_id: int = None, league_id: int = None) -> dict:
        """Sync all fantasy data (Leagues â†’ Divisions â†’ Teams â†’ Matches).

        Args:
            db: Database session
            real_competition_id: RealCompetitionID to sync. If None, derived from current season.
            league_id: Optional LeagueID to sync specific league only.

        Returns:
            Combined results from all sync operations.
        """
        all_results = {
            'status': 'success',
            'queries_executed': 0,
            'rows_affected': 0,
            'operations': {},
        }

        try:
            # Sync Leagues
            result = SyncService.sync_leagues(db, real_competition_id, league_id)
            all_results['operations']['sync_leagues'] = result
            all_results['queries_executed'] += result.get('queries_executed', 0)
            all_results['rows_affected'] += result.get('rows_affected', 0)
            if result.get('status') != 'success':
                all_results['status'] = 'partial'

            # Sync Divisions
            result = SyncService.sync_divisions(db, real_competition_id, league_id)
            all_results['operations']['sync_divisions'] = result
            all_results['queries_executed'] += result.get('queries_executed', 0)
            all_results['rows_affected'] += result.get('rows_affected', 0)
            if result.get('status') != 'success':
                all_results['status'] = 'partial'

            # Sync Teams
            result = SyncService.sync_teams(db, real_competition_id, league_id)
            all_results['operations']['sync_teams'] = result
            all_results['queries_executed'] += result.get('queries_executed', 0)
            all_results['rows_affected'] += result.get('rows_affected', 0)
            if result.get('status') != 'success':
                all_results['status'] = 'partial'

            # Sync Matches
            result = SyncService.sync_matches(db, real_competition_id, league_id)
            all_results['operations']['sync_matches'] = result
            all_results['queries_executed'] += result.get('queries_executed', 0)
            all_results['rows_affected'] += result.get('rows_affected', 0)
            if result.get('status') != 'success':
                all_results['status'] = 'partial'

        except Exception as e:
            all_results['status'] = 'error'
            all_results['error'] = str(e)

        return all_results

    @staticmethod
    def sync_real(db: Session, real_competition_id: int = None) -> dict:
        """Sync all Real* data (RealCompetitions â†’ RealTeams â†’ RealPlayers â†’ RealMatches â†’ RealTeamMembers â†’ RealStandings).

        Args:
            db: Database session
            real_competition_id: RealCompetitionID to sync. If None, derived from current season.

        Returns:
            Combined results from all sync operations.
        """
        all_results = {
            'status': 'success',
            'queries_executed': 0,
            'rows_affected': 0,
            'operations': {},
        }

        try:
            # Derive real_competition_id if not provided
            if not real_competition_id:
                real_competition_id = SyncService._get_real_competition_id(db)
                if not real_competition_id:
                    all_results['status'] = 'error'
                    all_results['error'] = 'Could not determine realCompetitionID'
                    return all_results

            # Sync RealCompetitions
            result = SyncService.sync_real_competitions(db)
            all_results['operations']['sync_real_competitions'] = result
            all_results['queries_executed'] += result.get('queries_executed', 0)
            all_results['rows_affected'] += result.get('rows_affected', 0)
            if result.get('status') != 'success':
                all_results['status'] = 'partial'

            # Sync RealTeams
            result = SyncService.sync_real_teams(db, real_competition_id)
            all_results['operations']['sync_real_teams'] = result
            all_results['queries_executed'] += result.get('queries_executed', 0)
            all_results['rows_affected'] += result.get('rows_affected', 0)
            if result.get('status') != 'success':
                all_results['status'] = 'partial'

            # Sync RealPlayers
            result = SyncService.sync_real_players(db, real_competition_id)
            all_results['operations']['sync_real_players'] = result
            all_results['queries_executed'] += result.get('queries_executed', 0)
            all_results['rows_affected'] += result.get('rows_affected', 0)
            if result.get('status') != 'success':
                all_results['status'] = 'partial'

            # Sync RealMatches
            result = SyncService.sync_real_matches(db, real_competition_id)
            all_results['operations']['sync_real_matches'] = result
            all_results['queries_executed'] += result.get('queries_executed', 0)
            all_results['rows_affected'] += result.get('rows_affected', 0)
            if result.get('status') != 'success':
                all_results['status'] = 'partial'

            # Sync RealTeamMembers
            result = SyncService.sync_real_team_members(db, real_competition_id)
            all_results['operations']['sync_real_team_members'] = result
            all_results['queries_executed'] += result.get('queries_executed', 0)
            all_results['rows_affected'] += result.get('rows_affected', 0)
            all_results['match_days_processed'] = result.get('match_days_processed', 0)
            if result.get('status') != 'success':
                all_results['status'] = 'partial'

            # Sync RealStandings
            result = SyncService.sync_real_standings(db, real_competition_id)
            all_results['operations']['sync_real_standings'] = result
            all_results['queries_executed'] += result.get('queries_executed', 0)
            all_results['rows_affected'] += result.get('rows_affected', 0)
            if result.get('status') != 'success':
                all_results['status'] = 'partial'

        except Exception as e:
            all_results['status'] = 'error'
            all_results['error'] = str(e)

        return all_results

    @staticmethod
    def sync_leagues(db: Session, real_competition_id: int = None, league_id: int = None) -> dict:
        """Sync Leagues with RealCompetitions.

        Args:
            db: Database session
            real_competition_id: RealCompetitionID to sync. If None, derived from current season.
            league_id: Optional LeagueID to sync specific league.
        """
        results = {
            'status': 'success',
            'queries_executed': 0,
            'rows_affected': 0,
        }

        try:
            # Derive real_competition_id if not provided
            if not real_competition_id and not league_id:
                real_competition_id = SyncService._get_real_competition_id(db)
                if not real_competition_id:
                    results['status'] = 'error'
                    results['error'] = 'Could not determine realCompetitionID'
                    return results

            # Build WHERE clause based on provided parameters
            where_conditions = []
            params = {}

            if league_id:
                where_conditions.append("`lg`.`leagueID` = :league_id")
                params['league_id'] = league_id

            if real_competition_id:
                where_conditions.append("(`rc`.`baseRealCompetitionID` = :real_competition_id OR `rc`.`extraRealCompetitionID` = :real_competition_id)")
                params['real_competition_id'] = real_competition_id

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            # Update Leagues with competition data
            q = text(f"""
                UPDATE `Leagues` `lg`
                   LEFT OUTER JOIN `RealCompetitions` `rc` ON `rc`.`realCompetitionID` = `rc`.`baseRealCompetitionID`
                   SET `lg`.`baseRealCompetitionID` = `rc`.`baseRealCompetitionID`,
                       `lg`.`extraRealCompetitionID` = `rc`.`extraRealCompetitionID`,
                       `lg`.`season` = `rc`.`realCompetitionSeasonId`
                   WHERE {where_clause}
            """)
            result = db.execute(q, params)
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)

        return results

    @staticmethod
    def sync_divisions(db: Session, real_competition_id: int = None, league_id: int = None) -> dict:
        """Sync Divisions with Leagues.

        Args:
            db: Database session
            real_competition_id: RealCompetitionID to sync. If None, derived from current season.
            league_id: Optional LeagueID to sync specific league's divisions.
        """
        results = {
            'status': 'success',
            'queries_executed': 0,
            'rows_affected': 0,
        }

        try:
            # Derive real_competition_id if not provided
            if not real_competition_id and not league_id:
                real_competition_id = SyncService._get_real_competition_id(db)
                if not real_competition_id:
                    results['status'] = 'error'
                    results['error'] = 'Could not determine realCompetitionID'
                    return results

            # Build WHERE clause based on provided parameters
            where_conditions = []
            params = {}

            if league_id:
                where_conditions.append("`dv`.`leagueID` = :league_id")
                params['league_id'] = league_id

            if real_competition_id:
                where_conditions.append("(`lg`.`baseRealCompetitionID` = :real_competition_id OR `lg`.`extraRealCompetitionID` = :real_competition_id)")
                params['real_competition_id'] = real_competition_id

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            # Update Divisions with league data
            q = text(f"""
                UPDATE `Divisions` `dv`
                   LEFT OUTER JOIN `Leagues` `lg` ON `lg`.`leagueID` = `dv`.`leagueID`
                   SET `dv`.`baseRealCompetitionID` = `lg`.`baseRealCompetitionID`,
                       `dv`.`extraRealCompetitionID` = `lg`.`extraRealCompetitionID`,
                       `dv`.`season` = `lg`.`season`,
                       `dv`.`seasonNum` = `lg`.`seasonNum`,
                       `dv`.`commissionerID` = `lg`.`commissionerID`,
                       `dv`.`prevLeagueID` = `lg`.`prevLeagueID`,
                       `dv`.`nextLeagueID` = `lg`.`nextLeagueID`
                   WHERE {where_clause}
            """)
            result = db.execute(q, params)
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)

        return results

    @staticmethod
    def sync_teams(db: Session, real_competition_id: int = None, league_id: int = None) -> dict:
        """Sync Teams with Divisions.

        Args:
            db: Database session
            real_competition_id: RealCompetitionID to sync. If None, derived from current season.
            league_id: Optional LeagueID to sync specific league's teams.
        """
        results = {
            'status': 'success',
            'queries_executed': 0,
            'rows_affected': 0,
        }

        try:
            # Derive real_competition_id if not provided
            if not real_competition_id and not league_id:
                real_competition_id = SyncService._get_real_competition_id(db)
                if not real_competition_id:
                    results['status'] = 'error'
                    results['error'] = 'Could not determine realCompetitionID'
                    return results

            # Build WHERE clause based on provided parameters
            where_conditions = []
            params = {}

            if league_id:
                where_conditions.append("`dv`.`leagueID` = :league_id")
                params['league_id'] = league_id

            if real_competition_id:
                where_conditions.append("(`dv`.`baseRealCompetitionID` = :real_competition_id OR `dv`.`extraRealCompetitionID` = :real_competition_id)")
                params['real_competition_id'] = real_competition_id

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            # Update Teams with division data
            q = text(f"""
                UPDATE `Teams` `tm`
                   LEFT OUTER JOIN `Divisions` `dv` ON `tm`.`divisionID` = `dv`.`divisionID`
                   SET `tm`.`baseRealCompetitionID` = `dv`.`baseRealCompetitionID`,
                       `tm`.`extraRealCompetitionID` = `dv`.`extraRealCompetitionID`,
                       `tm`.`season` = `dv`.`season`,
                       `tm`.`seasonNum` = `dv`.`seasonNum`,
                       `tm`.`divisionID` = `dv`.`divisionID`,
                       `tm`.`matchDayMapKey` = `dv`.`matchDayMapKey`,
                       `tm`.`leagueID` = `dv`.`leagueID`,
                       `tm`.`commissionerID` = `dv`.`commissionerID`,
                       `tm`.`prevLeagueID` = `dv`.`prevLeagueID`,
                       `tm`.`nextLeagueID` = `dv`.`nextLeagueID`,
                       `tm`.`prevDivisionID` = `dv`.`prevDivisionID`,
                       `tm`.`nextDivisionID` = `dv`.`nextDivisionID`,
                       `tm`.`leagueMatches` = `dv`.`leagueMatches`,
                       `tm`.`divisionMatches` = `dv`.`divisionMatches`
                   WHERE {where_clause}
            """)
            result = db.execute(q, params)
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)

        return results

    @staticmethod
    def sync_matches(db: Session, real_competition_id: int = None, league_id: int = None) -> dict:
        """Sync Matches and MatchTeams with Divisions/Teams.

        Args:
            db: Database session
            real_competition_id: RealCompetitionID to sync. If None, derived from current season.
            league_id: Optional LeagueID to sync specific league's matches.
        """
        results = {
            'status': 'success',
            'queries_executed': 0,
            'rows_affected': 0,
        }

        try:
            # Derive real_competition_id if not provided
            if not real_competition_id and not league_id:
                real_competition_id = SyncService._get_real_competition_id(db)
                if not real_competition_id:
                    results['status'] = 'error'
                    results['error'] = 'Could not determine realCompetitionID'
                    return results

            # Build WHERE clause based on provided parameters
            where_conditions = []
            params = {}

            if league_id:
                where_conditions.append("`dv`.`leagueID` = :league_id")
                params['league_id'] = league_id

            if real_competition_id:
                where_conditions.append("(`dv`.`baseRealCompetitionID` = :real_competition_id OR `dv`.`extraRealCompetitionID` = :real_competition_id)")
                params['real_competition_id'] = real_competition_id

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            # Update Matches with division data
            q1 = text(f"""
                UPDATE `Matches` `m`
                   LEFT OUTER JOIN `Divisions` `dv` ON `dv`.`divisionID` = `m`.`divisionID`
                   SET `m`.`leagueID` = `dv`.`leagueID`,
                       `m`.`season` = `dv`.`season`,
                       `m`.`seasonNum` = `dv`.`seasonNum`
                   WHERE {where_clause}
            """)
            result = db.execute(q1, params)
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

            # Update MatchTeams with team data
            # Build separate WHERE clause for MatchTeams (uses Teams table)
            where_conditions_mt = []
            params_mt = params.copy()

            if league_id:
                where_conditions_mt.append("`dv`.`leagueID` = :league_id")

            if real_competition_id:
                where_conditions_mt.append("(`t`.`baseRealCompetitionID` = :real_competition_id OR `t`.`extraRealCompetitionID` = :real_competition_id)")

            where_clause_mt = " AND ".join(where_conditions_mt) if where_conditions_mt else "1=1"

            q2 = text(f"""
                UPDATE `MatchTeams` `mt`
                   LEFT OUTER JOIN `Matches` `m` ON `m`.`matchID` = `mt`.`matchID`
                   LEFT OUTER JOIN `Divisions` `dv` ON `dv`.`divisionID` = `m`.`divisionID`
                   LEFT OUTER JOIN `Teams` `t` ON `t`.`teamID` = `mt`.`teamID`
                   SET `mt`.`userID` = `t`.`userID`,
                       `mt`.`teamName` = `t`.`teamName`,
                       `mt`.`teamSeeding` = CASE `m`.`competitionType`
                                               WHEN 1 THEN `t`.`seedingC1`
                                               WHEN 2 THEN `t`.`seedingC2`
                                               WHEN 3 THEN `t`.`seedingC3`
                                               ELSE NULL
                                            END,
                       `mt`.`matchDayMapKey` = `t`.`matchDayMapKey`
                   WHERE {where_clause_mt}
            """)
            result = db.execute(q2, params_mt)
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)

        return results

    @staticmethod
    def _load_real_competitions(db: Session, real_competition_id: int) -> dict:
        """Load RealCompetitions organized by SYMID.

        Args:
            db: Database session
            real_competition_id: RealCompetitionID (base or extra)

        Returns:
            Dict with BASE_SYMID and EXTRA_SYMID keys, or empty dict if not found
        """
        q = text("""
            SELECT *
            FROM `RealCompetitions`
            WHERE `baseRealCompetitionID` = :realCompetitionID
               OR `extraRealCompetitionID` = :realCompetitionID
        """)
        rows = db.execute(q, {'realCompetitionID': real_competition_id}).fetchall()

        real_comp = {}
        for row in rows:
            row_dict = dict(row._mapping) if hasattr(row, '_mapping') else dict(zip(row.keys(), row))
            symid = row_dict.get('realCompetitionSYMID')
            if symid == SyncService.BASE_SYMID:
                real_comp[SyncService.BASE_SYMID] = row_dict
            elif symid == SyncService.EXTRA_SYMID:
                real_comp[SyncService.EXTRA_SYMID] = row_dict

        return real_comp

    @staticmethod
    def sync_real_competitions(db: Session) -> dict:
        """Sync RealCompetitions and cascade to related tables."""
        results = {
            'status': 'success',
            'queries_executed': 0,
            'rows_affected': 0,
        }

        try:
            # Query #1: Update baseID and extraID
            q1 = text("""
                UPDATE `RealCompetitions` `rc`
                   INNER JOIN `RealCompetitions` `rc_b`
                      ON `rc_b`.`realCompetitionSeasonId` = `rc`.`realCompetitionSeasonId`
                      AND `rc_b`.`realCompetitionSYMID` = :baseRealCompetitionSYMID
                   INNER JOIN `RealCompetitions` `rc_e`
                      ON `rc_e`.`realCompetitionSeasonId` = `rc`.`realCompetitionSeasonId`
                      AND `rc_e`.`realCompetitionSYMID` = :extraRealCompetitionSYMID
                   SET `rc`.`baseRealCompetitionID` = `rc_b`.`realCompetitionID`,
                       `rc`.`extraRealCompetitionID` = `rc_e`.`realCompetitionID`
            """)
            result = db.execute(q1, {
                'baseRealCompetitionSYMID': SyncService.BASE_SYMID,
                'extraRealCompetitionSYMID': SyncService.EXTRA_SYMID,
            })
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

            # Query #2: Update prev and next
            q2 = text("""
                UPDATE `RealCompetitions` `c`
                   LEFT OUTER JOIN `RealCompetitions` `n`
                      ON `c`.`realCompetitionSYMID` = `n`.`realCompetitionSYMID`
                      AND CAST(`c`.`realCompetitionSeasonId` AS SIGNED) + 1 = CAST(`n`.`realCompetitionSeasonId` AS SIGNED)
                   LEFT OUTER JOIN `RealCompetitions` `p`
                      ON `c`.`realCompetitionSYMID` = `p`.`realCompetitionSYMID`
                      AND CAST(`c`.`realCompetitionSeasonId` AS SIGNED) - 1 = CAST(`p`.`realCompetitionSeasonId` AS SIGNED)
                   SET `c`.`prevRealCompetitionID` = `p`.`realCompetitionID`,
                       `c`.`nextRealCompetitionID` = `n`.`realCompetitionID`
            """)
            result = db.execute(q2)
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

            # Query #3: Update RealTeams
            q3 = text("""
                UPDATE `RealTeams` `t`
                   LEFT OUTER JOIN `RealCompetitions` `c` ON `c`.`realCompetitionID` = `t`.`realCompetitionID`
                   SET `t`.`realCompetitionUID` = `c`.`realCompetitionUID`,
                       `t`.`realCompetitionSYMID` = `c`.`realCompetitionSYMID`,
                       `t`.`realCompetitionSeasonId` = `c`.`realCompetitionSeasonId`,
                       `t`.`baseRealCompetitionID` = `c`.`baseRealCompetitionID`,
                       `t`.`extraRealCompetitionID` = `c`.`extraRealCompetitionID`
            """)
            result = db.execute(q3)
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

            # Query #4: Update RealMatches
            q4 = text("""
                UPDATE `RealMatches` `m`
                   LEFT OUTER JOIN `RealCompetitions` `c` ON `c`.`realCompetitionID` = `m`.`realCompetitionID`
                   SET `m`.`realCompetitionUID` = `c`.`realCompetitionUID`,
                       `m`.`realCompetitionSYMID` = `c`.`realCompetitionSYMID`,
                       `m`.`realCompetitionSeasonId` = `c`.`realCompetitionSeasonId`,
                       `m`.`realCompetitionFirstMatchDay` = `c`.`realCompetitionFirstMatchDay`,
                       `m`.`realCompetitionLastMatchDay` = `c`.`realCompetitionLastMatchDay`,
                       `m`.`baseRealCompetitionID` = `c`.`baseRealCompetitionID`,
                       `m`.`extraRealCompetitionID` = `c`.`extraRealCompetitionID`
            """)
            result = db.execute(q4)
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)

        return results

    @staticmethod
    def sync_real_teams(db: Session, real_competition_id: int) -> dict:
        """Sync RealTeams and populate RealTeamMembers."""
        results = {
            'status': 'success',
            'queries_executed': 0,
            'rows_affected': 0,
        }

        try:
            # Query #1: Set base fields
            q1 = text("""
                UPDATE `RealTeams` `t`
                   LEFT OUTER JOIN `RealTeams` `t1`
                      ON `t`.`baseRealCompetitionID` = `t1`.`realCompetitionID`
                      AND `t`.`realTeamUID` = `t1`.`realTeamUID`
                   SET `t`.`baseRealTeamID` = `t1`.`realTeamID`,
                       `t`.`baseRealTeamName` = `t1`.`realTeamName`,
                       `t`.`baseRealTeamShortName` = `t1`.`realTeamShortName`,
                       `t`.`realTeamMemberKey` = CONCAT('T', `t1`.`realTeamID`),
                       `t`.`draftPosition` = :draftPosition,
                       `t`.`draftPositionOrder` = 5,
                       `t`.`lastFDate` = IF(`t`.`lastF7Date` > `t`.`lastF42Date`, `t`.`lastF7Date`, `t`.`lastF42Date`)
                   WHERE `t`.`realCompetitionID` = :realCompetitionID
            """)
            result = db.execute(q1, {
                'realCompetitionID': real_competition_id,
                'draftPosition': RealTeamTypes.EPL_TEAM,
            })
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

            # Query #2: Update prev and next
            q2 = text("""
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
            """)
            result = db.execute(q2, {'realCompetitionID': real_competition_id})
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

            # Query #3: Insert new RealTeams to RealTeamMembers
            q3 = text("""
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
            """)
            result = db.execute(q3, {
                'realCompetitionID': real_competition_id,
                'draftPosition': RealTeamTypes.EPL_TEAM,
            })
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

            # Query #4: Update realTeamMemberID
            q4 = text("""
                UPDATE `RealTeams` `t`
                   LEFT OUTER JOIN `RealTeamMembers` `m` ON `m`.`realTeamMemberKey` = `t`.`realTeamMemberKey`
                   SET `t`.`realTeamMemberID` = `m`.`realTeamMemberID`
                   WHERE `t`.`realCompetitionID` = :realCompetitionID
            """)
            result = db.execute(q4, {'realCompetitionID': real_competition_id})
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

            # Query #5: Update old RealTeams to RealTeamMembers
            q5 = text("""
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
            """)
            result = db.execute(q5, {
                'realCompetitionID': real_competition_id,
                'draftPosition': RealTeamTypes.EPL_TEAM,
            })
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)

        return results

    @staticmethod
    def sync_real_players(db: Session, real_competition_id: int) -> dict:
        """Sync RealPlayers and populate RealTeamMembers."""
        results = {
            'status': 'success',
            'queries_executed': 0,
            'rows_affected': 0,
        }

        try:
            # Query #1: Set base fields
            q1 = text("""
                UPDATE `RealPlayers` `p`
                   LEFT OUTER JOIN `RealPlayers` `p1`
                      ON `p`.`baseRealCompetitionID` = `p1`.`realCompetitionID`
                      AND `p`.`realPlayerUID` = `p1`.`realPlayerUID`
                   SET `p`.`baseRealPlayerID` = `p1`.`realPlayerID`,
                       `p`.`realTeamMemberKey` = CONCAT('P', `p1`.`realPlayerID`)
                   WHERE `p`.`realCompetitionID` = :realCompetitionID
            """)
            result = db.execute(q1, {'realCompetitionID': real_competition_id})
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

            # Query #2: Sync from RealTeams
            q2 = text("""
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
            """)
            result = db.execute(q2, {'realCompetitionID': real_competition_id})
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

            # Query #3: Update prev and next
            q3 = text("""
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
            """)
            result = db.execute(q3, {'realCompetitionID': real_competition_id})
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

            # Query #4: Insert new RealPlayers to RealTeamMembers
            q4 = text("""
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
            """)
            result = db.execute(q4, {
                'realCompetitionID': real_competition_id,
                'dp_1': RealTeamMemberPositions.GOALKEEPER,
                'dp_2': RealTeamMemberPositions.DEFENDER,
                'dp_3': RealTeamMemberPositions.MIDFIELDER,
                'dp_4': RealTeamMemberPositions.STRIKER,
            })
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

            # Query #5: Update realTeamMemberID
            q5 = text("""
                UPDATE `RealPlayers` `p`
                   LEFT OUTER JOIN `RealTeamMembers` `m` ON `m`.`realTeamMemberKey` = `p`.`realTeamMemberKey`
                   SET `p`.`realTeamMemberID` = `m`.`realTeamMemberID`
                   WHERE `p`.`realCompetitionID` = :realCompetitionID
            """)
            result = db.execute(q5, {'realCompetitionID': real_competition_id})
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

            # Query #6: Update old RealPlayers to RealTeamMembers
            q6 = text("""
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
            """)
            result = db.execute(q6, {'realCompetitionID': real_competition_id})
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)

        return results

    @staticmethod
    def sync_real_matches(db: Session, real_competition_id: int) -> dict:
        """Sync RealMatchTeams with team information."""
        results = {
            'status': 'success',
            'queries_executed': 0,
            'rows_affected': 0,
        }

        try:
            # Query #1: Sync team info to RealMatchTeams
            q1 = text("""
                UPDATE `RealMatchTeams` `mt`
                   LEFT OUTER JOIN `RealTeams` `t` ON `t`.`realTeamID` = `mt`.`realTeamID`
                   SET `mt`.`realTeamMemberID` = `t`.`realTeamMemberID`,
                       `mt`.`realTeamMemberKey` = `t`.`realTeamMemberKey`,
                       `mt`.`realTeamUID` = `t`.`realTeamUID`,
                       `mt`.`realTeamName` = `t`.`realTeamName`,
                       `mt`.`realTeamShortName` = `t`.`realTeamShortName`,
                       `mt`.`realTeamSide` = `t`.`realTeamSide`,
                       `mt`.`realTeamNumber` = CASE `mt`.`realTeamSide`
                                                  WHEN 'Home' THEN 1
                                                  WHEN 'Away' THEN 2
                                                  ELSE NULL
                                               END
                   WHERE `mt`.`realCompetitionID` = :realCompetitionID
            """)
            result = db.execute(q1, {'realCompetitionID': real_competition_id})
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)

        return results

    @staticmethod
    def _sync_rmt_read_rs_teams(db: Session, rc: dict, matches: dict, match_day: int, teams: dict) -> None:
        """Read RealStandings teams data and update teams dict with calculated fields.

        Args:
            db: Database session
            rc: RealCompetition dict
            matches: Dict of matches keyed by realTeamMemberKey
            match_day: Match day number
            teams: Teams dict to update (modified in place)
        """
        comp_id = rc.get('realCompetitionID')

        # Query to get teams from RealStandings for this match day
        q = text("""
            SELECT `realStandingID`, `realTeamMemberKey`
            FROM `RealStandings`
            WHERE `realCompetitionID` = :comp_id
              AND `realCompetitionMatchDay` = :match_day
              AND LEFT(`realTeamMemberKey`, 1) = 'T'
        """)
        rows = db.execute(q, {
            'comp_id': comp_id,
            'match_day': match_day,
        }).fetchall()

        for row in rows:
            row_dict = dict(row._mapping) if hasattr(row, '_mapping') else dict(zip(row.keys(), row))
            key = row_dict.get('realTeamMemberKey')
            standing_id = row_dict.get('realStandingID')

            if key not in matches or key not in teams:
                continue

            # Extract match data
            score = matches[key].get('realTeamScore', 0)
            points = matches[key].get('realTeamPoints', 0)
            side = matches[key].get('realTeamSide', '')
            op_key = matches[key].get('op_realTeamMemberKey')
            op_score = matches[op_key].get('realTeamScore', 0) if op_key else 0

            # Calculate match result
            match_won = 1 if points == 3 else 0
            match_draw = 1 if points == 1 else 0
            match_lost = 1 if points == 0 else 0

            # Update teams dict with aggregated stats
            teams[key]['matchWon'] = match_won
            teams[key]['matchDraw'] = match_draw
            teams[key]['matchLost'] = match_lost
            teams[key]['played'] += 1
            teams[key]['won'] += match_won
            teams[key]['draw'] += match_draw
            teams[key]['lost'] += match_lost
            teams[key]['goalsFor'] += score
            teams[key]['goalsAgainst'] += op_score

            # Update home/away stats based on side
            if side:
                teams[key]['played' + side] += 1
                teams[key]['won' + side] += match_won
                teams[key]['draw' + side] += match_draw
                teams[key]['lost' + side] += match_lost
                teams[key]['goalsFor' + side] += score
                teams[key]['goalsAgainst' + side] += op_score

            # Aggregate points
            teams[key]['pointsL1'] += points

            # Store realStandingID for later updates
            teams[key]['realStandingID'] = standing_id

    @staticmethod
    def sync_real_team_members(db: Session, real_competition_id: int) -> dict:
        """Sync RealTeamMembers with match and player data across competitions.

        Args:
            db: Database session
            real_competition_id: RealCompetitionID to sync (base or extra)

        Returns:
            Results dict with status and operation counts
        """
        results = {
            'status': 'success',
            'queries_executed': 0,
            'rows_affected': 0,
            'match_days_processed': 0,
        }

        try:
            # Step 1: Load RealCompetitions and organize by SYMID
            q_comps = text("""
                SELECT *
                FROM `RealCompetitions`
                WHERE `baseRealCompetitionID` = :realCompetitionID
                   OR `extraRealCompetitionID` = :realCompetitionID
            """)
            comp_rows = db.execute(q_comps, {'realCompetitionID': real_competition_id}).fetchall()

            # Organize competitions by SYMID
            real_comp = {}
            for row in comp_rows:
                row_dict = dict(row._mapping) if hasattr(row, '_mapping') else dict(zip(row.keys(), row))
                symid = row_dict.get('realCompetitionSYMID')
                if symid == SyncService.BASE_SYMID:
                    real_comp[SyncService.BASE_SYMID] = row_dict
                elif symid == SyncService.EXTRA_SYMID:
                    real_comp[SyncService.EXTRA_SYMID] = row_dict

            if not real_comp:
                results['status'] = 'error'
                results['error'] = 'No RealCompetitions found for given ID'
                return results

            # Step 2: Load RealTeamMembers and separate into teams/players
            base_comp_id = real_comp.get(SyncService.BASE_SYMID, {}).get('realCompetitionID')
            extra_comp_id = real_comp.get(SyncService.EXTRA_SYMID, {}).get('realCompetitionID')

            q_members = text("""
                SELECT *
                FROM `RealTeamMembers`
                WHERE `baseRealCompetitionID` = :base_id
                  AND `extraRealCompetitionID` = :extra_id
            """)
            member_rows = db.execute(q_members, {
                'base_id': base_comp_id,
                'extra_id': extra_comp_id,
            }).fetchall()

            teams = {}
            players = {}
            for row in member_rows:
                row_dict = dict(row._mapping) if hasattr(row, '_mapping') else dict(zip(row.keys(), row))
                member_key = row_dict.get('realTeamMemberKey', '')

                if member_key.startswith('T'):
                    teams[member_key] = {
                        'realTeamMemberID': row_dict.get('realTeamMemberID'),
                        'prevRealTeamMemberKey': row_dict.get('prevRealTeamMemberKey'),
                        'nextRealTeamMemberKey': row_dict.get('nextRealTeamMemberKey'),
                        'baseRealCompetitionID': real_comp[SyncService.BASE_SYMID]['realCompetitionID'],
                        'extraRealCompetitionID': real_comp[SyncService.EXTRA_SYMID]['realCompetitionID'],
                        'isTeam': 1,
                        'isPlayer': 0,
                        'realTeamID': row_dict.get('realTeamID'),
                        'realTeamUID': row_dict.get('realTeamUID'),
                        'realTeamName': row_dict.get('realTeamName'),
                        'realTeamShortName': row_dict.get('realTeamShortName'),
                        'name': row_dict.get('name'),
                        'sortName': row_dict.get('sortName'),
                        'position': row_dict.get('position'),
                        'draftPosition': row_dict.get('draftPosition'),
                        'draftPositionOrder': row_dict.get('draftPositionOrder'),
                        'enabled': row_dict.get('enabled'),
                        'matchWon': 0,
                        'matchDraw': 0,
                        'matchLost': 0,
                        'played': 0,
                        'won': 0,
                        'draw': 0,
                        'lost': 0,
                        'goalsFor': 0,
                        'goalsAgainst': 0,
                        'place': 0,
                        'playedHome': 0,
                        'wonHome': 0,
                        'drawHome': 0,
                        'lostHome': 0,
                        'goalsForHome': 0,
                        'goalsAgainstHome': 0,
                        'placeHome': 0,
                        'playedAway': 0,
                        'wonAway': 0,
                        'drawAway': 0,
                        'lostAway': 0,
                        'goalsForAway': 0,
                        'goalsAgainstAway': 0,
                        'placeAway': 0,
                        'pointsL1': 0,
                        'ranking': 0
                    }
                elif member_key.startswith('P'):
                    players[member_key] = {
                        'realTeamMemberID': row_dict.get('realTeamMemberID'),
                        'prevRealTeamMemberKey': row_dict.get('prevRealTeamMemberKey'),
                        'nextRealTeamMemberKey': row_dict.get('nextRealTeamMemberKey'),
                        'baseRealCompetitionID': row_dict.get('baseRealCompetitionID'),
                        'extraRealCompetitionID': row_dict.get('extraRealCompetitionID'),
                        'isTeam': 0,
                        'isPlayer': 1,
                        'realTeamID': row_dict.get('realTeamID'),
                        'realPlayerID': row_dict.get('realPlayerID'),
                        'realPlayerUID': row_dict.get('realPlayerUID'),
                        'firstName': row_dict.get('firstName'),
                        'lastName': row_dict.get('lastName'),
                        'knownName': row_dict.get('knownName'),
                        'name': row_dict.get('name'),
                        'sortName': row_dict.get('sortName'),
                        'position': row_dict.get('position'),
                        'draftPosition': row_dict.get('draftPosition'),
                        'draftPositionOrder': row_dict.get('draftPositionOrder'),
                        'birthDate': row_dict.get('birthDate'),
                        'weight': row_dict.get('weight'),
                        'height': row_dict.get('height'),
                        'jerseyNumber': row_dict.get('jerseyNumber'),
                        'enabled': row_dict.get('enabled'),
                        'timePlayed': 0,
                        'gamePlayed': 0,
                        'goals': 0,
                        'assists': 0,
                        'yellowCards': 0,
                        'redCards': 0,
                        'goalsConceded': 0,
                        'cleanSheet': 0,
                        'pointsL1Played': 0,
                        'pointsL1GoalsAllowed': 0,
                        'pointsL1CleanSheet': 0,
                        'pointsL1Cards': 0,
                        'pointsL1Goals': 0,
                        'pointsL1Assists': 0,
                        'pointsL1OwnGoals': 0,
                        'pointsL1': 0,
                        'ranking': 0
                    }

            # Step 3: Process each competition and match day
            for rc_key, rc in real_comp.items():
                comp_id = rc.get('realCompetitionID')
                first_match_day = rc.get('realCompetitionFirstMatchDay', 1)
                last_match_day = rc.get('realCompetitionLastMatchDay', 1)

                for match_day in range(first_match_day, last_match_day + 1):
                    # Load matches for this match day
                    q_matches = text("""
                        SELECT `m`.`realMatchID`,
                               `m`.`realMatchStatus`,
                               `m`.`realMatchDate`,
                               `m`.`realMatchTime`,
                               `mt`.`realMatchTeamID`,
                               `mt`.`realTeamMemberKey`,
                               `mt`.`realTeamShortName`,
                               `mt`.`realTeamScore`,
                               `mt`.`realTeamPoints`,
                               `mt`.`realTeamSide`
                        FROM `RealMatches` `m`
                           INNER JOIN `RealMatchTeams` `mt` ON `mt`.`realMatchID` = `m`.`realMatchID`
                        WHERE `m`.`realCompetitionID` = :comp_id
                          AND `m`.`realCompetitionMatchDay` = :match_day
                    """)
                    match_rows = db.execute(q_matches, {
                        'comp_id': comp_id,
                        'match_day': match_day,
                    }).fetchall()

                    # Organize matches by team member key, tracking opposite teams
                    opposite = {}
                    matches = {}
                    for row in match_rows:
                        row_dict = dict(row._mapping) if hasattr(row, '_mapping') else dict(zip(row.keys(), row))
                        match_id = row_dict.get('realMatchID')
                        team_member_key = row_dict.get('realTeamMemberKey')

                        # Link opposite teams
                        if match_id in opposite:
                            row_dict['op_realTeamMemberKey'] = opposite[match_id]
                            matches[opposite[match_id]]['op_realTeamMemberKey'] = team_member_key
                        else:
                            opposite[match_id] = team_member_key

                        matches[team_member_key] = row_dict

                    # Sync team and player members for this match day
                    team_result = SyncService._sync_rmt_teams(db, rc, matches, match_day, teams)
                    results['rows_affected'] += team_result.get('rows_affected', 0)

                    player_result = SyncService._sync_rmt_players(db, rc, matches, match_day, teams, players)
                    results['rows_affected'] += player_result.get('rows_affected', 0)

                    results['match_days_processed'] += 1

        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)

        return results

    @staticmethod
    def _sync_rmt_teams(db: Session, rc: dict, matches: dict, match_day: int, teams: dict) -> dict:
        """Sync team members for a match day.

        Reads pre-calculated team data and updates/inserts RealStandings records.

        Args:
            db: Database session
            rc: RealCompetition dict
            matches: Dict of matches keyed by realTeamMemberKey
            match_day: Match day number
            teams: Teams dict with calculated stats (includes realStandingID if existing)

        Returns:
            Results dict with rows_affected
        """
        rows_affected = 0

        try:
            # Loop over teams and update/insert based on realStandingID
            for key, team_data in teams.items():
                if key not in matches:
                    continue

                op_key = matches[key].get('op_realTeamMemberKey')
                standing_id = team_data.get('realStandingID')

                # Build common parameters for both UPDATE and INSERT
                params = {
                    'realTeamMemberID': team_data.get('realTeamMemberID'),
                    'realTeamMemberKey': team_data.get('realTeamMemberKey'),
                    'prevRealTeamMemberKey': team_data.get('prevRealTeamMemberKey'),
                    'nextRealTeamMemberKey': team_data.get('nextRealTeamMemberKey'),
                    'realCompetitionID': rc.get('realCompetitionID'),
                    'realCompetitionUID': rc.get('realCompetitionUID'),
                    'realCompetitionSYMID': rc.get('realCompetitionSYMID'),
                    'realCompetitionSeasonId': rc.get('realCompetitionSeasonId'),
                    'realCompetitionMatchDay': match_day,
                    'realCompetitionLastMatchDay': rc.get('realCompetitionLastMatchDay'),
                    'baseRealCompetitionID': rc.get('baseRealCompetitionID'),
                    'extraRealCompetitionID': rc.get('extraRealCompetitionID'),
                    'baseMatchDay': match_day,
                    'realMatchID': matches[key].get('realMatchID'),
                    'realMatchTeamID': matches[key].get('realMatchTeamID'),
                    'realMatchDate': matches[key].get('realMatchDate'),
                    'realMatchTime': matches[key].get('realMatchTime'),
                    'realMatchStatus': matches[key].get('realMatchStatus'),
                    'realTeamID': team_data.get('realTeamID'),
                    'realTeamUID': team_data.get('realTeamUID'),
                    'realTeamName': team_data.get('realTeamName'),
                    'realTeamShortName': team_data.get('realTeamShortName'),
                    'realTeamScore': matches[key].get('realTeamScore'),
                    'realTeamSide': matches[key].get('realTeamSide'),
                    'oppositeRealTeamID': teams[op_key].get('realTeamID') if op_key else None,
                    'oppositeRealTeamUID': teams[op_key].get('realTeamUID') if op_key else None,
                    'oppositeRealTeamName': teams[op_key].get('realTeamName') if op_key else None,
                    'oppositeRealTeamShortName': teams[op_key].get('realTeamShortName') if op_key else None,
                    'oppositeRealTeamScore': matches[op_key].get('realTeamScore') if op_key else None,
                    'name': team_data.get('name'),
                    'sortName': team_data.get('sortName'),
                    'position': RealTeamTypes.EPL_TEAM,
                    'draftPosition': RealTeamTypes.EPL_TEAM,
                    'draftPositionOrder': 5,
                    'matchWon': team_data.get('matchWon', 0),
                    'matchDraw': team_data.get('matchDraw', 0),
                    'matchLost': team_data.get('matchLost', 0),
                    'matchPointsL1': matches[key].get('realTeamPoints', 0),
                    'livePointsL1': matches[key].get('realTeamPoints', 0),
                    'played': team_data.get('played', 0),
                    'won': team_data.get('won', 0),
                    'draw': team_data.get('draw', 0),
                    'lost': team_data.get('lost', 0),
                    'goalsFor': team_data.get('goalsFor', 0),
                    'goalsAgainst': team_data.get('goalsAgainst', 0),
                    'playedHome': team_data.get('playedHome', 0),
                    'wonHome': team_data.get('wonHome', 0),
                    'drawHome': team_data.get('drawHome', 0),
                    'lostHome': team_data.get('lostHome', 0),
                    'goalsForHome': team_data.get('goalsForHome', 0),
                    'goalsAgainstHome': team_data.get('goalsAgainstHome', 0),
                    'playedAway': team_data.get('playedAway', 0),
                    'wonAway': team_data.get('wonAway', 0),
                    'drawAway': team_data.get('drawAway', 0),
                    'lostAway': team_data.get('lostAway', 0),
                    'goalsForAway': team_data.get('goalsForAway', 0),
                    'goalsAgainstAway': team_data.get('goalsAgainstAway', 0),
                    'place': team_data.get('place', 0),
                    'placeHome': team_data.get('placeHome', 0),
                    'placeAway': team_data.get('placeAway', 0),
                    'pointsL1': team_data.get('pointsL1', 0),
                    'ranking': team_data.get('ranking', 0),
                }

                if standing_id:
                    # UPDATE existing record
                    params['standing_id'] = standing_id
                    q_update = text("""
                        UPDATE `RealStandings`
                        SET `realTeamMemberID` = :realTeamMemberID,
                            `realTeamMemberKey` = :realTeamMemberKey,
                            `prevRealTeamMemberKey` = :prevRealTeamMemberKey,
                            `nextRealTeamMemberKey` = :nextRealTeamMemberKey,
                            `realCompetitionID` = :realCompetitionID,
                            `realCompetitionUID` = :realCompetitionUID,
                            `realCompetitionSYMID` = :realCompetitionSYMID,
                            `realCompetitionSeasonId` = :realCompetitionSeasonId,
                            `realCompetitionMatchDay` = :realCompetitionMatchDay,
                            `realCompetitionLastMatchDay` = :realCompetitionLastMatchDay,
                            `baseRealCompetitionID` = :baseRealCompetitionID,
                            `extraRealCompetitionID` = :extraRealCompetitionID,
                            `isTeam` = 1,
                            `isPlayer` = 0,
                            `baseMatchDay` = :baseMatchDay,
                            `realMatchID` = :realMatchID,
                            `realMatchTeamID` = :realMatchTeamID,
                            `realMatchDate` = :realMatchDate,
                            `realMatchTime` = :realMatchTime,
                            `realMatchStatus` = :realMatchStatus,
                            `realTeamID` = :realTeamID,
                            `realTeamUID` = :realTeamUID,
                            `realTeamName` = :realTeamName,
                            `realTeamShortName` = :realTeamShortName,
                            `realTeamScore` = :realTeamScore,
                            `realTeamSide` = :realTeamSide,
                            `oppositeRealTeamID` = :oppositeRealTeamID,
                            `oppositeRealTeamUID` = :oppositeRealTeamUID,
                            `oppositeRealTeamName` = :oppositeRealTeamName,
                            `oppositeRealTeamShortName` = :oppositeRealTeamShortName,
                            `oppositeRealTeamScore` = :oppositeRealTeamScore,
                            `name` = :name,
                            `sortName` = :sortName,
                            `position` = :position,
                            `draftPosition` = :draftPosition,
                            `draftPositionOrder` = :draftPositionOrder,
                            `matchWon` = :matchWon,
                            `matchDraw` = :matchDraw,
                            `matchLost` = :matchLost,
                            `matchPointsL1` = :matchPointsL1,
                            `livePointsL1` = :livePointsL1,
                            `played` = :played,
                            `won` = :won,
                            `draw` = :draw,
                            `lost` = :lost,
                            `goalsFor` = :goalsFor,
                            `goalsAgainst` = :goalsAgainst,
                            `playedHome` = :playedHome,
                            `wonHome` = :wonHome,
                            `drawHome` = :drawHome,
                            `lostHome` = :lostHome,
                            `goalsForHome` = :goalsForHome,
                            `goalsAgainstHome` = :goalsAgainstHome,
                            `playedAway` = :playedAway,
                            `wonAway` = :wonAway,
                            `drawAway` = :drawAway,
                            `lostAway` = :lostAway,
                            `goalsForAway` = :goalsForAway,
                            `goalsAgainstAway` = :goalsAgainstAway,
                            `place` = :place,
                            `placeHome` = :placeHome,
                            `placeAway` = :placeAway,
                            `pointsL1` = :pointsL1,
                            `ranking` = :ranking,
                            `processed` = 1
                        WHERE `realStandingID` = :standing_id
                    """)
                    result = db.execute(q_update, params)
                    rows_affected += result.rowcount
                else:
                    # INSERT new record
                    q_insert = text("""
                        INSERT INTO `RealStandings`
                        (`realTeamMemberID`, `realTeamMemberKey`, `prevRealTeamMemberKey`, `nextRealTeamMemberKey`,
                         `realCompetitionID`, `realCompetitionUID`, `realCompetitionSYMID`, `realCompetitionSeasonId`,
                         `realCompetitionMatchDay`, `realCompetitionLastMatchDay`, `baseRealCompetitionID`, `extraRealCompetitionID`,
                         `isTeam`, `isPlayer`, `baseMatchDay`, `realMatchID`, `realMatchTeamID`, `realMatchDate`, `realMatchTime`,
                         `realMatchStatus`, `realTeamID`, `realTeamUID`, `realTeamName`, `realTeamShortName`, `realTeamScore`, `realTeamSide`,
                         `oppositeRealTeamID`, `oppositeRealTeamUID`, `oppositeRealTeamName`, `oppositeRealTeamShortName`, `oppositeRealTeamScore`,
                         `name`, `sortName`, `position`, `draftPosition`, `draftPositionOrder`,
                         `matchWon`, `matchDraw`, `matchLost`, `matchPointsL1`, `livePointsL1`,
                         `played`, `won`, `draw`, `lost`, `goalsFor`, `goalsAgainst`,
                         `playedHome`, `wonHome`, `drawHome`, `lostHome`, `goalsForHome`, `goalsAgainstHome`,
                         `playedAway`, `wonAway`, `drawAway`, `lostAway`, `goalsForAway`, `goalsAgainstAway`,
                         `place`, `placeHome`, `placeAway`, `pointsL1`, `ranking`, `processed`)
                        VALUES
                        (:realTeamMemberID, :realTeamMemberKey, :prevRealTeamMemberKey, :nextRealTeamMemberKey,
                         :realCompetitionID, :realCompetitionUID, :realCompetitionSYMID, :realCompetitionSeasonId,
                         :realCompetitionMatchDay, :realCompetitionLastMatchDay, :baseRealCompetitionID, :extraRealCompetitionID,
                         1, 0, :baseMatchDay, :realMatchID, :realMatchTeamID, :realMatchDate, :realMatchTime,
                         :realMatchStatus, :realTeamID, :realTeamUID, :realTeamName, :realTeamShortName, :realTeamScore, :realTeamSide,
                         :oppositeRealTeamID, :oppositeRealTeamUID, :oppositeRealTeamName, :oppositeRealTeamShortName, :oppositeRealTeamScore,
                         :name, :sortName, :position, :draftPosition, :draftPositionOrder,
                         :matchWon, :matchDraw, :matchLost, :matchPointsL1, :livePointsL1,
                         :played, :won, :draw, :lost, :goalsFor, :goalsAgainst,
                         :playedHome, :wonHome, :drawHome, :lostHome, :goalsForHome, :goalsAgainstHome,
                         :playedAway, :wonAway, :drawAway, :lostAway, :goalsForAway, :goalsAgainstAway,
                         :place, :placeHome, :placeAway, :pointsL1, :ranking, 1)
                    """)
                    result = db.execute(q_insert, params)
                    rows_affected += result.rowcount

        except Exception as e:
            return {'rows_affected': 0, 'error': str(e)}

        return {'rows_affected': rows_affected}
    @staticmethod
    def _sync_rmt_players(db: Session, rc: dict, matches: dict, match_day: int, teams: dict, players: dict) -> dict:
        """Sync player members for a match day.

        Reads pre-calculated player data and updates/inserts RealStandings records.

        Args:
            db: Database session
            rc: RealCompetition dict
            matches: Dict of matches keyed by realTeamMemberKey
            match_day: Match day number
            teams: Teams dict (for opposite team reference)
            players: Players dict with calculated stats (includes realStandingID if existing)

        Returns:
            Results dict with rows_affected
        """
        rows_affected = 0

        try:
            # Loop over players and update/insert based on realStandingID
            for key, player_data in players.items():
                # Construct team_key from player's realTeamID
                team_key = 'T' + str(player_data.get('realTeamID', ''))

                if team_key not in matches or team_key not in teams:
                    continue

                op_key = matches[team_key].get('op_realTeamMemberKey')
                standing_id = player_data.get('realStandingID')

                # Build common parameters for both UPDATE and INSERT
                params = {
                    'realTeamMemberID': player_data.get('realTeamMemberID'),
                    'realTeamMemberKey': player_data.get('realTeamMemberKey'),
                    'prevRealTeamMemberKey': player_data.get('prevRealTeamMemberKey'),
                    'nextRealTeamMemberKey': player_data.get('nextRealTeamMemberKey'),
                    'realCompetitionID': rc.get('realCompetitionID'),
                    'realCompetitionUID': rc.get('realCompetitionUID'),
                    'realCompetitionSYMID': rc.get('realCompetitionSYMID'),
                    'realCompetitionSeasonId': rc.get('realCompetitionSeasonId'),
                    'realCompetitionMatchDay': match_day,
                    'realCompetitionLastMatchDay': rc.get('realCompetitionLastMatchDay'),
                    'baseRealCompetitionID': rc.get('baseRealCompetitionID'),
                    'extraRealCompetitionID': rc.get('extraRealCompetitionID'),
                    'baseMatchDay': match_day,
                    'realMatchID': matches[team_key].get('realMatchID'),
                    'realMatchTeamID': matches[team_key].get('realMatchTeamID'),
                    'realMatchDate': matches[team_key].get('realMatchDate'),
                    'realMatchTime': matches[team_key].get('realMatchTime'),
                    'realMatchStatus': matches[team_key].get('realMatchStatus'),
                    'realTeamID': teams[team_key].get('realTeamID'),
                    'realTeamUID': teams[team_key].get('realTeamUID'),
                    'realTeamName': teams[team_key].get('realTeamName'),
                    'realTeamShortName': teams[team_key].get('realTeamShortName'),
                    'realTeamScore': teams[team_key].get('realTeamScore'),
                    'realTeamSide': teams[team_key].get('realTeamSide'),
                    'oppositeRealTeamID': teams[op_key].get('realTeamID') if op_key else None,
                    'oppositeRealTeamUID': teams[op_key].get('realTeamUID') if op_key else None,
                    'oppositeRealTeamName': teams[op_key].get('realTeamName') if op_key else None,
                    'oppositeRealTeamShortName': teams[op_key].get('realTeamShortName') if op_key else None,
                    'oppositeRealTeamScore': teams[op_key].get('realTeamScore') if op_key else None,
                    'realPlayerID': player_data.get('realPlayerID'),
                    'realPlayerUID': player_data.get('realPlayerUID'),
                    'firstName': player_data.get('firstName'),
                    'lastName': player_data.get('lastName'),
                    'knownName': player_data.get('knownName'),
                    'name': player_data.get('name'),
                    'sortName': player_data.get('sortName'),
                    'position': player_data.get('position'),
                    'draftPosition': player_data.get('draftPosition'),
                    'draftPositionOrder': player_data.get('draftPositionOrder'),
                    'timePlayed': player_data.get('timePlayed', 0),
                    'gamePlayed': player_data.get('gamePlayed', 0),
                    'goals': player_data.get('goals', 0),
                    'assists': player_data.get('assists', 0),
                    'yellowCards': player_data.get('yellowCards', 0),
                    'redCards': player_data.get('redCards', 0),
                    'goalsConceded': player_data.get('goalsConceded', 0),
                    'cleanSheet': player_data.get('cleanSheet', 0),
                    'pointsL1Played': player_data.get('pointsL1Played', 0),
                    'pointsL1GoalsAllowed': player_data.get('pointsL1GoalsAllowed', 0),
                    'pointsL1CleanSheet': player_data.get('pointsL1CleanSheet', 0),
                    'pointsL1Cards': player_data.get('pointsL1Cards', 0),
                    'pointsL1Goals': player_data.get('pointsL1Goals', 0),
                    'pointsL1Assists': player_data.get('pointsL1Assists', 0),
                    'pointsL1OwnGoals': player_data.get('pointsL1OwnGoals', 0),
                    'pointsL1': player_data.get('pointsL1', 0),
                    'livePointsL1': player_data.get('pointsL1', 0),
                    'ranking': player_data.get('ranking', 0),
                }

                if standing_id:
                    # UPDATE existing record
                    params['standing_id'] = standing_id
                    q_update = text("""
                        UPDATE `RealStandings`
                        SET `realTeamMemberID` = :realTeamMemberID,
                            `realTeamMemberKey` = :realTeamMemberKey,
                            `prevRealTeamMemberKey` = :prevRealTeamMemberKey,
                            `nextRealTeamMemberKey` = :nextRealTeamMemberKey,
                            `realCompetitionID` = :realCompetitionID,
                            `realCompetitionUID` = :realCompetitionUID,
                            `realCompetitionSYMID` = :realCompetitionSYMID,
                            `realCompetitionSeasonId` = :realCompetitionSeasonId,
                            `realCompetitionMatchDay` = :realCompetitionMatchDay,
                            `realCompetitionLastMatchDay` = :realCompetitionLastMatchDay,
                            `baseRealCompetitionID` = :baseRealCompetitionID,
                            `extraRealCompetitionID` = :extraRealCompetitionID,
                            `isTeam` = 0,
                            `isPlayer` = 1,
                            `baseMatchDay` = :baseMatchDay,
                            `realMatchID` = :realMatchID,
                            `realMatchTeamID` = :realMatchTeamID,
                            `realMatchDate` = :realMatchDate,
                            `realMatchTime` = :realMatchTime,
                            `realMatchStatus` = :realMatchStatus,
                            `realTeamID` = :realTeamID,
                            `realTeamUID` = :realTeamUID,
                            `realTeamName` = :realTeamName,
                            `realTeamShortName` = :realTeamShortName,
                            `realTeamScore` = :realTeamScore,
                            `realTeamSide` = :realTeamSide,
                            `oppositeRealTeamID` = :oppositeRealTeamID,
                            `oppositeRealTeamUID` = :oppositeRealTeamUID,
                            `oppositeRealTeamName` = :oppositeRealTeamName,
                            `oppositeRealTeamShortName` = :oppositeRealTeamShortName,
                            `oppositeRealTeamScore` = :oppositeRealTeamScore,
                            `realPlayerID` = :realPlayerID,
                            `realPlayerUID` = :realPlayerUID,
                            `firstName` = :firstName,
                            `lastName` = :lastName,
                            `knownName` = :knownName,
                            `name` = :name,
                            `sortName` = :sortName,
                            `position` = :position,
                            `draftPosition` = :draftPosition,
                            `draftPositionOrder` = :draftPositionOrder,
                            `timePlayed` = :timePlayed,
                            `gamePlayed` = :gamePlayed,
                            `goals` = :goals,
                            `assists` = :assists,
                            `yellowCards` = :yellowCards,
                            `redCards` = :redCards,
                            `goalsConceded` = :goalsConceded,
                            `cleanSheet` = :cleanSheet,
                            `pointsL1Played` = :pointsL1Played,
                            `pointsL1GoalsAllowed` = :pointsL1GoalsAllowed,
                            `pointsL1CleanSheet` = :pointsL1CleanSheet,
                            `pointsL1Cards` = :pointsL1Cards,
                            `pointsL1Goals` = :pointsL1Goals,
                            `pointsL1Assists` = :pointsL1Assists,
                            `pointsL1OwnGoals` = :pointsL1OwnGoals,
                            `pointsL1` = :pointsL1,
                            `livePointsL1` = :livePointsL1,
                            `ranking` = :ranking,
                            `processed` = 1
                        WHERE `realStandingID` = :standing_id
                    """)
                    result = db.execute(q_update, params)
                    rows_affected += result.rowcount
                else:
                    # INSERT new record
                    q_insert = text("""
                        INSERT INTO `RealStandings`
                        (`realTeamMemberID`, `realTeamMemberKey`, `prevRealTeamMemberKey`, `nextRealTeamMemberKey`,
                         `realCompetitionID`, `realCompetitionUID`, `realCompetitionSYMID`, `realCompetitionSeasonId`,
                         `realCompetitionMatchDay`, `realCompetitionLastMatchDay`, `baseRealCompetitionID`, `extraRealCompetitionID`,
                         `isTeam`, `isPlayer`, `baseMatchDay`, `realMatchID`, `realMatchTeamID`, `realMatchDate`, `realMatchTime`,
                         `realMatchStatus`, `realTeamID`, `realTeamUID`, `realTeamName`, `realTeamShortName`, `realTeamScore`, `realTeamSide`,
                         `oppositeRealTeamID`, `oppositeRealTeamUID`, `oppositeRealTeamName`, `oppositeRealTeamShortName`, `oppositeRealTeamScore`,
                         `realPlayerID`, `realPlayerUID`, `firstName`, `lastName`, `knownName`, `name`, `sortName`, `position`, `draftPosition`,
                         `draftPositionOrder`, `timePlayed`, `gamePlayed`, `goals`, `assists`, `yellowCards`, `redCards`, `goalsConceded`, `cleanSheet`,
                         `pointsL1Played`, `pointsL1GoalsAllowed`, `pointsL1CleanSheet`, `pointsL1Cards`, `pointsL1Goals`, `pointsL1Assists`,
                         `pointsL1OwnGoals`, `pointsL1`, `livePointsL1`, `ranking`, `processed`)
                        VALUES
                        (:realTeamMemberID, :realTeamMemberKey, :prevRealTeamMemberKey, :nextRealTeamMemberKey,
                         :realCompetitionID, :realCompetitionUID, :realCompetitionSYMID, :realCompetitionSeasonId,
                         :realCompetitionMatchDay, :realCompetitionLastMatchDay, :baseRealCompetitionID, :extraRealCompetitionID,
                         0, 1, :baseMatchDay, :realMatchID, :realMatchTeamID, :realMatchDate, :realMatchTime,
                         :realMatchStatus, :realTeamID, :realTeamUID, :realTeamName, :realTeamShortName, :realTeamScore, :realTeamSide,
                         :oppositeRealTeamID, :oppositeRealTeamUID, :oppositeRealTeamName, :oppositeRealTeamShortName, :oppositeRealTeamScore,
                         :realPlayerID, :realPlayerUID, :firstName, :lastName, :knownName, :name, :sortName, :position, :draftPosition,
                         :draftPositionOrder, :timePlayed, :gamePlayed, :goals, :assists, :yellowCards, :redCards, :goalsConceded, :cleanSheet,
                         :pointsL1Played, :pointsL1GoalsAllowed, :pointsL1CleanSheet, :pointsL1Cards, :pointsL1Goals, :pointsL1Assists,
                         :pointsL1OwnGoals, :pointsL1, :livePointsL1, :ranking, 1)
                    """)
                    result = db.execute(q_insert, params)
                    rows_affected += result.rowcount

        except Exception as e:
            return {'rows_affected': 0, 'error': str(e)}

        return {'rows_affected': rows_affected}
    @staticmethod
    def sync_real_standings(db: Session, real_competition_id: int) -> dict:
        """Sync RealTeamMembers with data from RealStandings.

        Updates both last season data and current season data in RealTeamMembers
        based on the last match day of each competition.

        Args:
            db: Database session
            real_competition_id: RealCompetitionID to sync (base or extra)

        Returns:
            Results dict with status and rows_affected
        """
        rows_affected = 0

        try:
            # Load RealCompetitions organized by SYMID
            real_comp = SyncService._load_real_competitions(db, real_competition_id)

            if not real_comp or SyncService.BASE_SYMID not in real_comp:
                return {
                    'status': 'error',
                    'error': 'Could not load RealCompetitions',
                    'rows_affected': 0,
                }

            base_comp_id = real_comp[SyncService.BASE_SYMID]['realCompetitionID']

            # Query #1: Update last_* fields from previous season
            q1 = text("""
                UPDATE `RealTeamMembers` `rtm`
                   LEFT OUTER JOIN `RealStandings` `rs`
                      ON `rs`.`realTeamMemberKey` = `rtm`.`prevRealTeamMemberKey`
                      AND `rs`.`realCompetitionMatchDay` = `rs`.`realCompetitionLastMatchDay`
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
                   WHERE `rtm`.`baseRealCompetitionID` = :base_comp_id
            """)
            result = db.execute(q1, {'base_comp_id': base_comp_id})
            rows_affected += result.rowcount

            # Query #2: Update current season fields from current standings
            q2 = text("""
                UPDATE `RealTeamMembers` `rtm`
                   LEFT OUTER JOIN `RealStandings` `rs`
                      ON `rs`.`realTeamMemberKey` = `rtm`.`realTeamMemberKey`
                      AND `rs`.`realCompetitionMatchDay` = `rs`.`realCompetitionLastMatchDay`
                   SET `rtm`.`timePlayed` = `rs`.`timePlayed`,
                       `rtm`.`gamePlayed` = `rs`.`gamePlayed`,
                       `rtm`.`goals` = `rs`.`goals`,
                       `rtm`.`assists` = `rs`.`assists`,
                       `rtm`.`yellowCards` = `rs`.`yellowCards`,
                       `rtm`.`redCards` = `rs`.`redCards`,
                       `rtm`.`goalsConceded` = `rs`.`goalsConceded`,
                       `rtm`.`cleanSheet` = `rs`.`cleanSheet`,
                       `rtm`.`played` = `rs`.`played`,
                       `rtm`.`won` = `rs`.`won`,
                       `rtm`.`draw` = `rs`.`draw`,
                       `rtm`.`lost` = `rs`.`lost`,
                       `rtm`.`goalsFor` = `rs`.`goalsFor`,
                       `rtm`.`goalsAgainst` = `rs`.`goalsAgainst`,
                       `rtm`.`pointsL1` = `rs`.`pointsL1`,
                       `rtm`.`livePointsL1` = `rs`.`livePointsL1`,
                       `rtm`.`ranking` = `rs`.`ranking`
                   WHERE `rtm`.`baseRealCompetitionID` = :base_comp_id
            """)
            result = db.execute(q2, {'base_comp_id': base_comp_id})
            rows_affected += result.rowcount

            return {
                'status': 'success',
                'rows_affected': rows_affected,
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'rows_affected': 0,
            }

    @staticmethod
    def _sync_rmt_read_rs_players(db: Session, rc: dict, matches: dict, match_day: int, teams: dict, players: dict) -> None:
        """Read RealStandings players data and update players dict with match statistics.

        Args:
            db: Database session
            rc: RealCompetition dict
            matches: Dict of matches keyed by realTeamMemberKey
            match_day: Match day number
            teams: Teams dict (for reference)
            players: Players dict to update (modified in place)
        """
        comp_id = rc.get('realCompetitionID')

        # Query to get players from RealStandings for this match day
        q = text("""
            SELECT `realStandingID`,
                   `realTeamMemberKey`,
                   `matchTimePlayed`,
                   `matchGamePlayed`,
                   `matchGoals`,
                   `matchAssists`,
                   `matchYellowCards`,
                   `matchRedCards`,
                   `matchGoalsConceded`,
                   `matchCleanSheet`,
                   `matchPointsL1Played`,
                   `matchPointsL1GoalsAllowed`,
                   `matchPointsL1CleanSheet`,
                   `matchPointsL1Cards`,
                   `matchPointsL1Goals`,
                   `matchPointsL1Assists`,
                   `matchPointsL1OwnGoals`,
                   `matchPointsL1`
            FROM `RealStandings`
            WHERE `realCompetitionID` = :comp_id
              AND `realCompetitionMatchDay` = :match_day
              AND LEFT(`realTeamMemberKey`, 1) = 'P'
        """)
        rows = db.execute(q, {
            'comp_id': comp_id,
            'match_day': match_day,
        }).fetchall()

        for row in rows:
            row_dict = dict(row._mapping) if hasattr(row, '_mapping') else dict(zip(row.keys(), row))
            key = row_dict.get('realTeamMemberKey')
            standing_id = row_dict.get('realStandingID')

            if key not in players:
                continue

            # Aggregate match statistics
            players[key]['timePlayed'] += row_dict.get('matchTimePlayed', 0)
            players[key]['gamePlayed'] += row_dict.get('matchGamePlayed', 0)
            players[key]['goals'] += row_dict.get('matchGoals', 0)
            players[key]['assists'] += row_dict.get('matchAssists', 0)
            players[key]['yellowCards'] += row_dict.get('matchYellowCards', 0)
            players[key]['redCards'] += row_dict.get('matchRedCards', 0)
            players[key]['goalsConceded'] += row_dict.get('matchGoalsConceded', 0)
            players[key]['cleanSheet'] += row_dict.get('matchCleanSheet', 0)

            # Aggregate points breakdown
            players[key]['pointsL1Played'] += row_dict.get('matchPointsL1Played', 0)
            players[key]['pointsL1GoalsAllowed'] += row_dict.get('matchPointsL1GoalsAllowed', 0)
            players[key]['pointsL1CleanSheet'] += row_dict.get('matchPointsL1CleanSheet', 0)
            players[key]['pointsL1Cards'] += row_dict.get('matchPointsL1Cards', 0)
            players[key]['pointsL1Goals'] += row_dict.get('matchPointsL1Goals', 0)
            players[key]['pointsL1Assists'] += row_dict.get('matchPointsL1Assists', 0)
            players[key]['pointsL1OwnGoals'] += row_dict.get('matchPointsL1OwnGoals', 0)
            players[key]['pointsL1'] += row_dict.get('matchPointsL1', 0)

            # Store realStandingID for later updates
            players[key]['realStandingID'] = standing_id

    @staticmethod
    def _sync_rmt_calc_places(teams: dict) -> None:
        """Calculate league positions for teams across all/home/away sides.

        Args:
            teams: Teams dict to update (modified in place)
        """
        for side in ["", "Home", "Away"]:
            data = []
            for team_key, team in teams.items():
                data.append({
                    "key": team["realTeamMemberKey"],
                    "pts": team['pointsL1'],
                    "diff": team["goalsFor" + side] - team["goalsAgainst" + side],
                    "goals": team["goalsFor" + side],
                    "name": team["name"]
                })

            # Sort by: points (desc), goal difference (desc), goals (desc), name (asc)
            sorted_data = sorted(data, key=lambda x: (-x['pts'], -x['diff'], -x['goals'], x['name']))

            # Assign places
            for i, item in enumerate(sorted_data):
                teams[item["key"]]["place" + side] = i + 1

    @staticmethod
    def _sync_rmt_calc_ranking(teams: dict, players: dict) -> None:
        """Calculate overall rankings for teams and players combined.

        Args:
            teams: Teams dict to update (modified in place)
            players: Players dict to update (modified in place)
        """
        data = []

        # Add teams to ranking pool
        for team_key, team in teams.items():
            data.append({
                "key": team["realTeamMemberKey"],
                "pts": team['pointsL1'],
                "name": team["name"]
            })

        # Add players to ranking pool
        for player_key, player in players.items():
            data.append({
                "key": player["realTeamMemberKey"],
                "pts": player['pointsL1'],
                "name": player["name"]
            })

        # Sort by: points (desc), name (asc)
        sorted_data = sorted(data, key=lambda x: (-x['pts'], x['name']))

        # Assign rankings
        for i, item in enumerate(sorted_data):
            if item["key"].startswith("T"):
                teams[item["key"]]["ranking"] = i + 1
            elif item["key"].startswith("P"):
                players[item["key"]]["ranking"] = i + 1


