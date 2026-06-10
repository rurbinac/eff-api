"""Fantasy league synchronization service.

Syncs application-level fantasy data across Leagues, Divisions, Teams, and Matches.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text


class SyncFantasyService:
    """Synchronize application-level fantasy data."""

    @staticmethod
    def _get_real_competition_id(db: Session) -> int:
        """Get realCompetitionID for current season (EN_PR).

        Args:
            db: Database session

        Returns:
            realCompetitionID or None if not found
        """
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
            'symid': 'EN_PR',
        }).first()

        return result[0] if result else None

    @staticmethod
    def sync_fantasy(db: Session, real_competition_id: int = None, league_id: int = None) -> dict:
        """Sync all fantasy data (Leagues → Divisions → Teams → Matches).

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
            result = SyncFantasyService.sync_leagues(db, real_competition_id, league_id)
            all_results['operations']['sync_leagues'] = result
            all_results['queries_executed'] += result.get('queries_executed', 0)
            all_results['rows_affected'] += result.get('rows_affected', 0)
            if result.get('status') != 'success':
                all_results['status'] = 'partial'

            # Sync Divisions
            result = SyncFantasyService.sync_divisions(db, real_competition_id, league_id)
            all_results['operations']['sync_divisions'] = result
            all_results['queries_executed'] += result.get('queries_executed', 0)
            all_results['rows_affected'] += result.get('rows_affected', 0)
            if result.get('status') != 'success':
                all_results['status'] = 'partial'

            # Sync Teams
            result = SyncFantasyService.sync_teams(db, real_competition_id, league_id)
            all_results['operations']['sync_teams'] = result
            all_results['queries_executed'] += result.get('queries_executed', 0)
            all_results['rows_affected'] += result.get('rows_affected', 0)
            if result.get('status') != 'success':
                all_results['status'] = 'partial'

            # Sync Matches
            result = SyncFantasyService.sync_matches(db, real_competition_id, league_id)
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
                real_competition_id = SyncFantasyService._get_real_competition_id(db)
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
                real_competition_id = SyncFantasyService._get_real_competition_id(db)
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
                real_competition_id = SyncFantasyService._get_real_competition_id(db)
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
                real_competition_id = SyncFantasyService._get_real_competition_id(db)
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
