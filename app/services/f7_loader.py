"""F7 OPTA feed loader - loads single match detailed results."""

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.f7_parser import F7Parser


class F7Loader:
    """Load F7 parsed data into the database (foundation layer for both quick and full modes)."""

    @staticmethod
    def load_file(db: Session, file_path: str, mode: str = 'quick') -> dict:
        """Parse and load an F7 file - foundation layer.

        Args:
            db: Database session
            file_path: Path to the F7 XML file
            mode: 'quick' or 'full' (for future use, foundation is same for both)

        Returns:
            Dictionary with match/teams/players data and caches for mode-specific processing
        """
        # Parse the file
        parsed_data = F7Parser.parse_file(file_path)

        # Get RealCompetitions record
        try:
            real_competition_id = F7Loader._get_real_competition(db, parsed_data['competition'])
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Failed to get RealCompetitions: {str(e)}",
                'match_id': parsed_data.get('match_id'),
            }

        # Build teams cache
        try:
            teams_cache = F7Loader._build_teams_cache(db, real_competition_id, parsed_data['match_data'])
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Failed to build teams cache: {str(e)}",
                'match_id': parsed_data.get('match_id'),
            }

        # Get match IDs
        try:
            match_ids = F7Loader._get_match_ids(db, real_competition_id, teams_cache)
            if not match_ids:
                return {
                    'status': 'no_match',
                    'message': 'Match not found in database',
                    'match_id': parsed_data.get('match_id'),
                }
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Failed to get match IDs: {str(e)}",
                'match_id': parsed_data.get('match_id'),
            }

        # Build players cache
        try:
            players_cache = F7Loader._build_players_cache(db, real_competition_id, parsed_data['players'])
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Failed to build players cache: {str(e)}",
                'match_id': parsed_data.get('match_id'),
            }

        # Return foundation data for mode-specific processing
        return {
            'status': 'ready',
            'mode': mode,
            'match_id': parsed_data.get('match_id'),
            'real_competition_id': real_competition_id,
            'competition': parsed_data['competition'],
            'match_data': parsed_data['match_data'],
            'match_ids': match_ids,
            'teams_cache': teams_cache,
            'players_cache': players_cache,
        }

    @staticmethod
    def _get_real_competition(db: Session, competition: dict) -> int:
        """Get RealCompetitions record ID."""
        symid = competition.get('symid')
        season_id = competition.get('season_id')

        if not (symid and season_id):
            raise ValueError("Missing symid or season_id in competition data")

        query = text("""
            SELECT realCompetitionID
            FROM `RealCompetitions`
            WHERE realCompetitionSYMID = :symid
              AND realCompetitionSeasonId = :season_id
            LIMIT 1
        """)

        result = db.execute(query, {
            'symid': symid,
            'season_id': season_id,
        }).first()

        if not result:
            raise ValueError(f"RealCompetition not found for {symid}/{season_id}")

        return result[0]

    @staticmethod
    def _build_teams_cache(db: Session, real_competition_id: int, match_data: dict) -> dict:
        """Build teams cache from RealTeams table."""
        home_team_uid = match_data.get('home_team_ref')
        away_team_uid = match_data.get('away_team_ref')

        if not (home_team_uid and away_team_uid):
            raise ValueError("Missing home or away team reference in match data")

        query = text("""
            SELECT `realTeamID`, `realTeamUID`, `realTeamMemberKey`
            FROM `RealTeams`
            WHERE `realCompetitionID` = :comp_id
              AND (`realTeamUID` = :home_uid OR `realTeamUID` = :away_uid)
        """)

        results = db.execute(query, {
            'comp_id': real_competition_id,
            'home_uid': home_team_uid,
            'away_uid': away_team_uid,
        }).mappings().all()

        teams_cache = {}
        for row in results:
            teams_cache[row['realTeamUID']] = {
                'realTeamID': row['realTeamID'],
                'realTeamMemberKey': row['realTeamMemberKey'],
            }

        return teams_cache

    @staticmethod
    def _get_match_ids(db: Session, real_competition_id: int, teams_cache: dict) -> dict | None:
        """Get RealMatch and RealMatchTeam IDs."""
        # Get one team UID from each side
        team_uids = list(teams_cache.keys())
        if len(team_uids) < 2:
            return None

        home_uid = team_uids[0]
        away_uid = team_uids[1]

        query = text("""
            SELECT `m`.`realMatchID` AS `mID`,
                   `t1`.`realMatchTeamID` AS `mtID_Home`,
                   `t2`.`realMatchTeamID` AS `mtID_Away`
            FROM `RealMatches` `m`
            INNER JOIN `RealMatchTeams` `t1` ON `m`.`realMatchID` = `t1`.`realMatchID`
                AND `t1`.`realTeamNumber` = 1
            INNER JOIN `RealMatchTeams` `t2` ON `m`.`realMatchID` = `t2`.`realMatchID`
                AND `t2`.`realTeamNumber` = 2
            WHERE `m`.`realCompetitionID` = :comp_id
              AND `t1`.`realTeamUID` = :home_uid
              AND `t2`.`realTeamUID` = :away_uid
            LIMIT 1
        """)

        result = db.execute(query, {
            'comp_id': real_competition_id,
            'home_uid': home_uid,
            'away_uid': away_uid,
        }).first()

        if not result:
            return None

        return {
            'realMatchID': result[0],
            'realMatchTeamID_Home': result[1],
            'realMatchTeamID_Away': result[2],
        }

    @staticmethod
    def _build_players_cache(db: Session, real_competition_id: int, players: dict) -> dict:
        """Build players cache from RealPlayers table."""
        # Start with player data from XML
        players_cache = {}
        for player_uid, player_data in players.items():
            players_cache[player_uid] = {
                'realPlayerUID': player_uid,
                'realTeamMemberKey': None,
                'realTeamUID': player_data.get('realTeamUID'),
                'firstName': player_data.get('firstName'),
                'lastName': player_data.get('lastName'),
                'knownName': player_data.get('knownName'),
                'position': player_data.get('position'),
            }

        # Enrich with database data
        if not players_cache:
            return players_cache

        player_uids = list(players_cache.keys())

        # Build IN clause for query
        placeholders = ','.join([f':uid_{i}' for i in range(len(player_uids))])
        params = {f'uid_{i}': uid for i, uid in enumerate(player_uids)}
        params['comp_id'] = real_competition_id

        query_str = f"""
            SELECT `realPlayerID`, `realPlayerUID`, `realTeamMemberKey`
            FROM `RealPlayers`
            WHERE `realCompetitionID` = :comp_id
              AND `realPlayerUID` IN ({placeholders})
        """

        results = db.execute(text(query_str), params).mappings().all()

        for row in results:
            player_uid = row['realPlayerUID']
            if player_uid in players_cache:
                players_cache[player_uid]['realPlayerID'] = row['realPlayerID']
                players_cache[player_uid]['realTeamMemberKey'] = row['realTeamMemberKey']

        return players_cache
