"""F7 OPTA feed loader - loads single match detailed results."""

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.f7_parser import F7Parser
from app.services.f7_events import add_event, load_goal, load_booking, load_substitution
from app.constants import RealMatchPeriod


class F7Loader:
    """Load F7 parsed data into the database (foundation layer for both quick and full modes)."""

    @staticmethod
    def load_file(db: Session, file_path: str, mode: str = 'quick') -> dict:
        """Parse and load an F7 file with mode-specific persistence.

        Args:
            db: Database session
            file_path: Path to the F7 XML file
            mode: 'quick' or 'full'

        Returns:
            Dictionary with processing result status
        """
        # Phase 1: Foundation layer (get caches)
        foundation = F7Loader._get_foundation(db, file_path)
        if foundation['status'] != 'ready':
            return foundation

        # Phase 2: Process F7 data into in-memory structures
        try:
            processed_data = F7Loader._process_f7_data(
                foundation['parsed_data'],
                foundation['real_competition_id'],
                foundation['teams_cache'],
                foundation['players_cache']
            )
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Failed to process F7 data: {str(e)}",
                'match_id': foundation['parsed_data'].get('match_id'),
            }

        # Phase 3: Persist based on mode
        if mode == 'quick':
            return F7Loader._save_quick_mode(db, foundation, processed_data)
        elif mode == 'full':
            return F7Loader._save_full_mode(db, foundation, processed_data)
        else:
            return {
                'status': 'error',
                'error': f"Unknown mode: {mode}",
                'match_id': foundation['parsed_data'].get('match_id'),
            }

    @staticmethod
    def _get_foundation(db: Session, file_path: str) -> dict:
        """Get foundation layer data (caches and match IDs)."""
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

        # Build players cache with lineup data
        try:
            player_lineup = parsed_data['match_data'].get('player_lineup', {})
            match_time = parsed_data['match_data'].get('match_time')
            players_cache = F7Loader._build_players_cache(
                db, real_competition_id, parsed_data['players'],
                player_lineup, match_time
            )
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Failed to build players cache: {str(e)}",
                'match_id': parsed_data.get('match_id'),
            }

        return {
            'status': 'ready',
            'parsed_data': parsed_data,
            'real_competition_id': real_competition_id,
            'match_ids': match_ids,
            'teams_cache': teams_cache,
            'players_cache': players_cache,
        }

    @staticmethod
    def _process_f7_data(parsed_data: dict, real_competition_id: int,
                        teams_cache: dict, players_cache: dict) -> dict:
        """Process F7 data into in-memory structures.

        Returns:
            Dictionary with processed data:
            - match_events: List of match events with eventKey for deduplication
            - standings_data: Player standings/performance data
        """
        # Extract match data
        match_data = parsed_data.get('match_data', {})

        # Initialize events cache for processing
        events_cache = []

        # Process goals from parsed data
        goals = match_data.get('goals', [])
        for goal_data in goals:
            events_cache = load_goal(events_cache, goal_data['element'], goal_data['team_uid'])

        # Process bookings from parsed data
        bookings = match_data.get('bookings', [])
        for booking_data in bookings:
            events_cache = load_booking(events_cache, booking_data['element'], booking_data['team_uid'])

        # Process substitutions from parsed data
        substitutions = match_data.get('substitutions', [])
        for sub_data in substitutions:
            events_cache = load_substitution(events_cache, sub_data['element'], sub_data['team_uid'])

        # Sort events by eventKey (period, time, timestamp, class)
        events_cache.sort(key=lambda e: e.get('eventKey', ''))

        # Placeholder for standings data (user will provide logic)
        standings_data = {}

        return {
            'match_data': match_data,
            'match_events': events_cache,
            'standings_data': standings_data,
        }

    @staticmethod
    def _save_quick_mode(db: Session, foundation: dict, processed_data: dict) -> dict:
        """Save data in Quick mode (updates only).

        Quick mode updates:
        - RealMatches
        - RealMatchTeams
        - RealMatchEvents (insert/update)
        - RealStandings (to be implemented)
        """
        match_ids = foundation['match_ids']
        match_data = processed_data['match_data']
        match_events = processed_data['match_events']

        results = {
            'status': 'success',
            'match_id': foundation['parsed_data'].get('match_id'),
            'matches_updated': 0,
            'match_teams_updated': 0,
            'match_events_processed': 0,
            'standings_updated': 0,
        }

        try:
            # Update RealMatches
            F7Loader.update_match_quick_mode(db, match_ids, match_data)
            results['matches_updated'] = 1
        except Exception as e:
            results['errors'] = results.get('errors', [])
            results['errors'].append(f"RealMatches update failed: {str(e)}")

        try:
            # Update RealMatchTeams
            teams_result = F7Loader.update_match_teams_quick_mode(
                db, match_ids, match_data, foundation['teams_cache']
            )
            results['match_teams_updated'] = teams_result.get('teams_updated', 0)
        except Exception as e:
            results['errors'] = results.get('errors', [])
            results['errors'].append(f"RealMatchTeams update failed: {str(e)}")

        # TODO: Process RealMatchEvents (insert/update)
        # TODO: Update RealStandings

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            results['status'] = 'error'
            results['errors'] = results.get('errors', [])
            results['errors'].append(f"Commit failed: {str(e)}")

        return results

    @staticmethod
    def _save_full_mode(db: Session, foundation: dict, processed_data: dict) -> dict:
        """Save data in Full mode (complete updates).

        Full mode updates: All tables with complete data
        """
        # TODO: Implement full mode persistence
        return {
            'status': 'not_implemented',
            'message': 'Full mode implementation pending',
            'match_id': foundation['parsed_data'].get('match_id'),
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
    def _build_players_cache(db: Session, real_competition_id: int, players: dict,
                            player_lineup: dict = None, match_time: int = None) -> dict:
        """Build players cache from RealPlayers table and PlayerLineUp data."""
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
        if players_cache:
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

        # Enrich with PlayerLineUp data
        if player_lineup:
            for player_ref, lineup_info in player_lineup.items():
                if player_ref in players_cache:
                    status = lineup_info.get('status')
                    shirt_number = lineup_info.get('shirt_number')
                    formation_place = lineup_info.get('formation_place')

                    players_cache[player_ref]['status'] = status
                    players_cache[player_ref]['formation_place'] = formation_place
                    players_cache[player_ref]['shirt_number'] = shirt_number

                    # Initialize performance tracking fields
                    players_cache[player_ref]['assists'] = 0
                    players_cache[player_ref]['goals'] = 0
                    players_cache[player_ref]['goalsConceded'] = 0
                    players_cache[player_ref]['ownGoals'] = 0
                    players_cache[player_ref]['position'] = 0
                    players_cache[player_ref]['redCards'] = 0
                    players_cache[player_ref]['secondYellowCards'] = 0
                    players_cache[player_ref]['straightRedCards'] = 0
                    players_cache[player_ref]['yellowCards'] = 0
                    players_cache[player_ref]['pointsAssists'] = 0
                    players_cache[player_ref]['pointsCards'] = 0
                    players_cache[player_ref]['pointsCleanSheet'] = 0
                    players_cache[player_ref]['pointsGoals'] = 0
                    players_cache[player_ref]['pointsGoalsAllowed'] = 0
                    players_cache[player_ref]['pointsOwnGoals'] = 0
                    players_cache[player_ref]['pointsPlayed'] = 0

                    # Calculate playing time and flags based on status
                    if status == 'Start':
                        # Player started the match
                        players_cache[player_ref]['timeIn'] = 0
                        players_cache[player_ref]['timeOut'] = match_time
                        players_cache[player_ref]['timePlayed'] = match_time
                        players_cache[player_ref]['startedGame'] = 1
                        players_cache[player_ref]['finishedGame'] = 1
                        players_cache[player_ref]['fullGame'] = 1
                        players_cache[player_ref]['gamePlayed'] = 1
                        players_cache[player_ref]['cleanSheet'] = 1
                    else:
                        # Player is a substitute
                        players_cache[player_ref]['timeIn'] = None
                        players_cache[player_ref]['timeOut'] = None
                        players_cache[player_ref]['timePlayed'] = 0
                        players_cache[player_ref]['startedGame'] = 0
                        players_cache[player_ref]['finishedGame'] = 0
                        players_cache[player_ref]['fullGame'] = 0
                        players_cache[player_ref]['gamePlayed'] = 0
                        players_cache[player_ref]['cleanSheet'] = 0

        return players_cache

    @staticmethod
    def update_match_quick_mode(db: Session, match_ids: dict, match_data: dict) -> dict:
        """Update RealMatches with F7 data in Quick mode.

        Args:
            db: Database session
            match_ids: Dict with realMatchID from foundation layer
            match_data: Parsed match data from F7

        Returns:
            Dict with update status and count
        """
        now = datetime.utcnow()

        # Extract and normalize period data
        period = RealMatchPeriod.get_period(match_data.get('period'))
        real_match_status = RealMatchPeriod.to_match_status(period)
        real_match_ended = RealMatchPeriod.to_match_ended(period)

        # Parse date - extract UTC version
        match_date = match_data.get('date')
        if match_date:
            # Convert to ISO format (YYYY-MM-DD HH:MM:SS) removing timezone info
            try:
                # Format: 20250519T200000+0100 -> extract date/time part
                if 'T' in match_date:
                    date_part = match_date.split('T')[0]
                    time_part = match_data.get('date').split('T')[1].split('+')[0].split('-')[0]
                    match_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} {time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
            except:
                pass

        # Extract attendance (convert to int or None)
        attendance = None
        attendance_str = match_data.get('attendance')
        if attendance_str:
            try:
                attendance = int(attendance_str)
            except (ValueError, TypeError):
                pass

        # Convert match times to int or None
        def safe_int(value):
            try:
                return int(value) if value else None
            except (ValueError, TypeError):
                return None

        match_time = safe_int(match_data.get('match_time'))
        first_half_time = safe_int(match_data.get('first_half_time'))
        second_half_time = safe_int(match_data.get('second_half_time'))

        # Update RealMatches
        update_query = text("""
            UPDATE `RealMatches`
            SET realMatchStatus = :status,
                realMatchType = :match_type,
                realMatchPeriod = :period,
                realMatchRealPeriod = :real_period,
                realMatchAttendance = :attendance,
                realMatchDate = :match_date,
                realMatchDateOffset = :date_offset,
                realMatchResultType = :result_type,
                realMatchTime = :match_time,
                realMatchFirstHalfTime = :first_half_time,
                realMatchSecondHalfTime = :second_half_time,
                realMatchEnded = :match_ended,
                lastF7Date = :now,
                lastFDate = :now,
                updatedIn = :now
            WHERE realMatchID = :match_id
        """)

        db.execute(update_query, {
            'match_id': match_ids['realMatchID'],
            'status': real_match_status,
            'match_type': match_data.get('match_type'),
            'period': period,
            'real_period': match_data.get('period'),
            'attendance': attendance,
            'match_date': match_date,
            'date_offset': match_data.get('date_offset'),
            'result_type': match_data.get('result_type'),
            'match_time': match_time,
            'first_half_time': first_half_time,
            'second_half_time': second_half_time,
            'match_ended': real_match_ended,
            'now': now,
        })

        return {'status': 'updated', 'match_id': match_ids['realMatchID']}

    @staticmethod
    def update_match_teams_quick_mode(db: Session, match_ids: dict, match_data: dict,
                                      teams_cache: dict) -> dict:
        """Update RealMatchTeams with F7 data in Quick mode.

        Args:
            db: Database session
            match_ids: Dict with realMatchID, realMatchTeamID_Home, realMatchTeamID_Away
            match_data: Parsed match data from F7
            teams_cache: Teams cache with team info

        Returns:
            Dict with update status
        """
        now = datetime.utcnow()

        # Get scores
        home_score_str = match_data.get('home_score')
        away_score_str = match_data.get('away_score')

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
                'realMatchTeamID': match_ids['realMatchTeamID_Home'],
                'team_number': 1,
                'my_score': home_score,
                'other_score': away_score,
            },
            {
                'realMatchTeamID': match_ids['realMatchTeamID_Away'],
                'team_number': 2,
                'my_score': away_score,
                'other_score': home_score,
            },
        ]

        update_count = 0

        for team_update in teams_to_update:
            # Calculate points and result
            points = 0
            result = None

            if team_update['my_score'] is not None and team_update['other_score'] is not None:
                if team_update['my_score'] > team_update['other_score']:
                    points = 3
                    result = 1  # Win
                elif team_update['my_score'] == team_update['other_score']:
                    points = 1
                    result = 0  # Draw
                else:
                    points = 0
                    result = -1  # Loss

            # Update RealMatchTeams
            update_query = text("""
                UPDATE `RealMatchTeams`
                SET realTeamScore = :score,
                    realTeamRealScore = :score,
                    realTeamResult = :result,
                    realTeamPoints = :points,
                    updatedIn = :now
                WHERE realMatchTeamID = :mt_id
            """)

            db.execute(update_query, {
                'mt_id': team_update['realMatchTeamID'],
                'score': team_update['my_score'],
                'result': result,
                'points': points,
                'now': now,
            })

            update_count += 1

        return {'status': 'updated', 'teams_updated': update_count}
