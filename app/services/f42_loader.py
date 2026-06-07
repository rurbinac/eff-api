"""F42 OPTA feed loader - loads data into the database."""

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.f42_parser import F42Parser
from app.constants import DraftPositions


class F42Loader:
    """Load F42 parsed data into the database."""

    @staticmethod
    def load_file(db: Session, file_path: str) -> dict:
        """Parse and load an F42 file into the database.

        Args:
            db: Database session
            file_path: Path to the F42 XML file

        Returns:
            Dictionary with statistics: competitions_inserted, competitions_updated, etc.
        """
        # Parse the file
        parsed_data = F42Parser.parse_file(file_path)

        # Load data
        stats = {
            'competitions_inserted': 0,
            'competitions_updated': 0,
            'teams_inserted': 0,
            'teams_updated': 0,
            'players_inserted': 0,
            'players_updated': 0,
            'matches_inserted': 0,
            'matches_updated': 0,
            'errors': [],
        }

        # Load competitions
        comp_data = parsed_data['competition']
        try:
            comp_result = F42Loader._load_competition(db, comp_data)
            stats['competitions_inserted'] += comp_result['inserted']
            stats['competitions_updated'] += comp_result['updated']
            real_competition_id = comp_result['real_competition_id']
        except Exception as e:
            stats['errors'].append(f"Error loading competition: {str(e)}")
            return stats

        # Load teams
        team_id_mapping = {}
        try:
            teams_result = F42Loader._load_teams(db, parsed_data['teams'], real_competition_id)
            stats['teams_inserted'] += teams_result['inserted']
            stats['teams_updated'] += teams_result['updated']
            team_id_mapping = teams_result.get('team_uid_mapping', {})
        except Exception as e:
            stats['errors'].append(f"Error loading teams: {str(e)}")

        # Load players
        try:
            players_result = F42Loader._load_players(db, parsed_data['players'], real_competition_id, team_id_mapping)
            stats['players_inserted'] += players_result['inserted']
            stats['players_updated'] += players_result['updated']
        except Exception as e:
            stats['errors'].append(f"Error loading players: {str(e)}")

        # Pre-load existing matches cache
        matches_cache = {}
        try:
            matches_cache = F42Loader._load_matches_cache(db, real_competition_id)
        except Exception as e:
            stats['errors'].append(f"Error loading matches cache: {str(e)}")

        # Build teams cache from loaded teams
        teams_cache = {}
        for team_data in parsed_data['teams']:
            team_uid = team_data.get('uID')
            if team_uid in team_id_mapping:
                real_team_id = team_id_mapping[team_uid]
                # Query for team details
                team_query = text("""
                    SELECT realTeamID, realTeamName, realTeamShortName
                    FROM `RealTeams`
                    WHERE realCompetitionID = :comp_id AND realTeamUID = :uid
                    LIMIT 1
                """)
                team_result = db.execute(team_query, {
                    'comp_id': real_competition_id,
                    'uid': team_uid,
                }).first()
                if team_result:
                    teams_cache[team_uid] = list(team_result)

        # Load matches
        try:
            matches_result = F42Loader._load_matches(db, parsed_data['matches'], real_competition_id,
                                                      matches_cache, teams_cache, comp_data)
            stats['matches_inserted'] += matches_result['inserted']
            stats['matches_updated'] += matches_result['updated']
        except Exception as e:
            stats['errors'].append(f"Error loading matches: {str(e)}")

        # Commit changes
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            stats['errors'].append(f"Error committing changes: {str(e)}")
            return stats

        return stats

    @staticmethod
    def _load_competition(db: Session, comp_data: dict) -> dict:
        """Load or update a competition in RealCompetitions."""
        real_competition_symid = comp_data.get('competition_code')
        real_competition_season_id = comp_data.get('season_id')
        competition_id = comp_data.get('competition_id')
        country = comp_data.get('country', 'England')

        if not (real_competition_symid and real_competition_season_id):
            raise ValueError("Missing competition_code or season_id")

        # Build realCompetitionUID
        real_competition_uid = f"c{competition_id}" if competition_id else None

        # Query for existing competition
        query = text("""
            SELECT realCompetitionID
            FROM `RealCompetitions`
            WHERE realCompetitionSYMID = :symid
              AND realCompetitionSeasonId = :season_id
            LIMIT 1
        """)

        result = db.execute(query, {
            'symid': real_competition_symid,
            'season_id': real_competition_season_id,
        }).first()

        now = datetime.utcnow()

        if result:
            # Update existing
            real_competition_id = result[0]
            update_query = text("""
                UPDATE `RealCompetitions`
                SET updatedIn = :now
                WHERE realCompetitionID = :id
            """)
            db.execute(update_query, {'id': real_competition_id, 'now': now})
            return {
                'inserted': 0,
                'updated': 1,
                'real_competition_id': real_competition_id,
            }
        else:
            # Insert new
            insert_query = text("""
                INSERT INTO `RealCompetitions`
                (realCompetitionUID, realCompetitionSYMID, realCompetitionSeasonId, realCompetitionCountry, createdIn, updatedIn)
                VALUES (:uid, :symid, :season_id, :country, :now, :now)
            """)
            db.execute(insert_query, {
                'uid': real_competition_uid,
                'symid': real_competition_symid,
                'season_id': real_competition_season_id,
                'country': country,
                'now': now,
            })
            db.flush()

            # Get the inserted ID
            result = db.execute(text("""
                SELECT realCompetitionID
                FROM `RealCompetitions`
                WHERE realCompetitionSYMID = :symid
                  AND realCompetitionSeasonId = :season_id
                LIMIT 1
            """), {
                'symid': real_competition_symid,
                'season_id': real_competition_season_id,
            }).first()

            real_competition_id = result[0] if result else None
            return {
                'inserted': 1,
                'updated': 0,
                'real_competition_id': real_competition_id,
            }

    @staticmethod
    def _load_teams(db: Session, teams_data: list, real_competition_id: int) -> dict:
        """Load or update teams in RealTeams.

        Returns:
            Dictionary with inserted, updated counts and team_uid_mapping
        """
        inserted = 0
        updated = 0
        now = datetime.utcnow()
        team_uid_mapping = {}  # Map team uID to realTeamID for later use

        # Get competition details for defaults
        comp_query = text("""
            SELECT realCompetitionUID, realCompetitionSYMID, realCompetitionSeasonId, realCompetitionCountry, baseRealCompetitionID, extraRealCompetitionID
            FROM `RealCompetitions`
            WHERE realCompetitionID = :id
            LIMIT 1
        """)
        comp_result = db.execute(comp_query, {'id': real_competition_id}).first()
        if not comp_result:
            raise ValueError(f"RealCompetition {real_competition_id} not found")

        comp_uid, comp_symid, season_id, comp_country, base_real_comp_id, extra_real_comp_id = comp_result

        for team_data in teams_data:
            real_team_uid = team_data.get('uID')
            real_team_name = team_data.get('name')
            real_team_symid = team_data.get('symid')

            if not (real_team_uid and real_team_name):
                continue

            # Query for existing team
            query = text("""
                SELECT realTeamID
                FROM `RealTeams`
                WHERE realCompetitionID = :comp_id
                  AND realTeamUID = :uid
                LIMIT 1
            """)

            result = db.execute(query, {
                'comp_id': real_competition_id,
                'uid': real_team_uid,
            }).first()

            if result:
                # Update existing
                real_team_id = result[0]
                update_query = text("""
                    UPDATE `RealTeams`
                    SET realTeamName = :name,
                        realTeamSYMID = :symid,
                        realTeamShortName = :short_name,
                        lastF42Date = :now,
                        lastFDate = :now,
                        updatedIn = :now
                    WHERE realTeamID = :id
                """)
                db.execute(update_query, {
                    'id': real_team_id,
                    'name': real_team_name,
                    'symid': real_team_symid,
                    'short_name': real_team_symid,
                    'now': now,
                })
                updated += 1
            else:
                # Insert new
                insert_query = text("""
                    INSERT INTO `RealTeams`
                    (realCompetitionID, realCompetitionUID, realCompetitionSYMID, realCompetitionSeasonId,
                     baseRealCompetitionID, extraRealCompetitionID,
                     realTeamUID, realTeamName, realTeamSYMID, realTeamShortName, realTeamCountry,
                     position, draftPosition, draftPositionOrder,
                     isProcessedMember,
                     lastF42Date, lastFDate,
                     createdIn, updatedIn)
                    VALUES (:comp_id, :comp_uid, :comp_symid, :season_id,
                            :base_comp_id, :extra_comp_id,
                            :uid, :name, :symid, :short_name, :country,
                            :position, :draft_position, :draft_position_order,
                            :is_processed,
                            :now, :now,
                            :now, :now)
                """)
                db.execute(insert_query, {
                    'comp_id': real_competition_id,
                    'comp_uid': comp_uid,
                    'comp_symid': comp_symid,
                    'season_id': season_id,
                    'base_comp_id': base_real_comp_id,
                    'extra_comp_id': extra_real_comp_id,
                    'uid': real_team_uid,
                    'name': real_team_name,
                    'symid': real_team_symid,
                    'short_name': real_team_symid,
                    'country': comp_country,
                    'position': 'EPLTeam',
                    'draft_position': 'EPLTeam',
                    'draft_position_order': 5,
                    'is_processed': 0,
                    'now': now,
                })
                inserted += 1
                # Get the inserted realTeamID
                result = db.execute(text("""
                    SELECT realTeamID
                    FROM `RealTeams`
                    WHERE realCompetitionID = :comp_id AND realTeamUID = :uid
                    LIMIT 1
                """), {'comp_id': real_competition_id, 'uid': real_team_uid}).first()
                if result:
                    team_uid_mapping[real_team_uid] = result[0]

            # Also store existing team IDs in mapping
            if result and real_team_uid not in team_uid_mapping:
                team_uid_mapping[real_team_uid] = real_team_id

        return {
            'inserted': inserted,
            'updated': updated,
            'team_uid_mapping': team_uid_mapping,
        }

    @staticmethod
    def _load_players(db: Session, players_data: list, real_competition_id: int, team_uid_mapping: dict) -> dict:
        """Load or update players in RealPlayers."""
        inserted = 0
        updated = 0
        now = datetime.utcnow()

        # Get competition details
        comp_query = text("""
            SELECT realCompetitionUID, realCompetitionSYMID, realCompetitionSeasonId, baseRealCompetitionID, extraRealCompetitionID
            FROM `RealCompetitions`
            WHERE realCompetitionID = :id
            LIMIT 1
        """)
        comp_result = db.execute(comp_query, {'id': real_competition_id}).first()
        if not comp_result:
            raise ValueError(f"RealCompetition {real_competition_id} not found")

        comp_uid, comp_symid, season_id, base_real_comp_id, extra_real_comp_id = comp_result

        for player_data in players_data:
            real_player_uid = player_data.get('uID')
            team_uid = player_data.get('team_uID')

            if not (real_player_uid and team_uid):
                continue

            # Get realTeamID from mapping
            real_team_id = team_uid_mapping.get(team_uid)
            if not real_team_id:
                continue

            # Get realTeamUID from RealTeams
            team_query = text("""
                SELECT realTeamUID
                FROM `RealTeams`
                WHERE realCompetitionID = :comp_id AND realTeamID = :team_id
                LIMIT 1
            """)
            team_result = db.execute(team_query, {
                'comp_id': real_competition_id,
                'team_id': real_team_id,
            }).first()
            if not team_result:
                continue

            real_team_uid = team_result[0]

            # Check for existing player
            query = text("""
                SELECT realPlayerID
                FROM `RealPlayers`
                WHERE realCompetitionID = :comp_id
                  AND realPlayerUID = :player_uid
                LIMIT 1
            """)

            result = db.execute(query, {
                'comp_id': real_competition_id,
                'player_uid': real_player_uid,
            }).first()

            # Extract player data
            first_name = player_data.get('first_name')
            last_name = player_data.get('last_name')
            known_name = player_data.get('known_name')
            position = player_data.get('position')
            real_position = player_data.get('real_position')

            # Convert numeric fields safely
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
                if not value or value.lower() == 'unknown':
                    return None
                try:
                    # Validate it's a proper date format (YYYY-MM-DD)
                    from datetime import datetime as dt
                    dt.strptime(value, '%Y-%m-%d')
                    return value
                except (ValueError, TypeError):
                    return None

            birth_date = safe_date(player_data.get('birth_date'))
            weight = safe_float(player_data.get('weight'))
            height = safe_float(player_data.get('height'))
            jersey_number = safe_int(player_data.get('jersey_number'))

            # Calculate draft position order and name
            draft_position_order = DraftPositions.get_order(position, real_position)
            draft_position = DraftPositions.get_position(draft_position_order) if draft_position_order else None

            if result:
                # Update existing
                real_player_id = result[0]
                update_query = text("""
                    UPDATE `RealPlayers`
                    SET firstName = :first_name,
                        lastName = :last_name,
                        knownName = :known_name,
                        position = :position,
                        realPosition = :real_position,
                        birthDate = :birth_date,
                        weight = :weight,
                        height = :height,
                        jerseyNumber = :jersey_number,
                        draftPosition = :draft_position,
                        draftPositionOrder = :draft_pos_order,
                        lastF42Date = :now,
                        lastFDate = :now,
                        updatedIn = :now
                    WHERE realPlayerID = :id
                """)
                db.execute(update_query, {
                    'id': real_player_id,
                    'first_name': first_name,
                    'last_name': last_name,
                    'known_name': known_name,
                    'position': position,
                    'real_position': real_position,
                    'birth_date': birth_date,
                    'weight': weight,
                    'height': height,
                    'jersey_number': jersey_number,
                    'draft_position': draft_position,
                    'draft_pos_order': draft_position_order,
                    'now': now,
                })
                updated += 1
            else:
                # Insert new
                insert_query = text("""
                    INSERT INTO `RealPlayers`
                    (realCompetitionID, realCompetitionUID, realCompetitionSYMID, realCompetitionSeasonId,
                     baseRealCompetitionID, extraRealCompetitionID,
                     realTeamID, realTeamUID,
                     realPlayerUID, firstName, lastName, knownName,
                     position, realPosition,
                     birthDate, weight, height, jerseyNumber,
                     draftPosition, draftPositionOrder,
                     isProcessedMember,
                     lastF42Date, lastFDate,
                     createdIn, updatedIn)
                    VALUES (:comp_id, :comp_uid, :comp_symid, :season_id,
                            :base_comp_id, :extra_comp_id,
                            :team_id, :team_uid,
                            :player_uid, :first_name, :last_name, :known_name,
                            :position, :real_position,
                            :birth_date, :weight, :height, :jersey_number,
                            :draft_position, :draft_pos_order,
                            :is_processed,
                            :now, :now,
                            :now, :now)
                """)
                db.execute(insert_query, {
                    'comp_id': real_competition_id,
                    'comp_uid': comp_uid,
                    'comp_symid': comp_symid,
                    'season_id': season_id,
                    'base_comp_id': base_real_comp_id,
                    'extra_comp_id': extra_real_comp_id,
                    'team_id': real_team_id,
                    'team_uid': real_team_uid,
                    'player_uid': real_player_uid,
                    'first_name': first_name,
                    'last_name': last_name,
                    'known_name': known_name,
                    'position': position,
                    'real_position': real_position,
                    'birth_date': birth_date,
                    'weight': weight,
                    'height': height,
                    'jersey_number': jersey_number,
                    'draft_position': draft_position,
                    'draft_pos_order': draft_position_order,
                    'is_processed': 0,
                    'now': now,
                })
                inserted += 1

        return {'inserted': inserted, 'updated': updated}

    @staticmethod
    def _load_matches_cache(db: Session, real_competition_id: int) -> dict:
        """Pre-load existing RealMatches and RealMatchTeams IDs into a cache.

        Returns:
            Dictionary with key="tUID_1,tUID_2" → [realMatchID, mtID_1, mtID_2]
        """
        cache = {}

        query_text = text("""
            SELECT `m`.`realMatchID` AS `mID`,
                   `t1`.`realMatchTeamID` AS `mtID_1`,
                   `t2`.`realMatchTeamID` AS `mtID_2`,
                   `t1`.`realTeamUID` AS `tUID_1`,
                   `t2`.`realTeamUID` AS `tUID_2`
            FROM `RealMatches` `m`
            INNER JOIN `RealMatchTeams` `t1` ON `m`.`realMatchID` = `t1`.`realMatchID`
                AND `t1`.`realTeamNumber` = 1
            INNER JOIN `RealMatchTeams` `t2` ON `m`.`realMatchID` = `t2`.`realMatchID`
                AND `t2`.`realTeamNumber` = 2
            WHERE `m`.`realCompetitionID` = :realCompetitionID
        """)

        results = db.execute(query_text, {'realCompetitionID': real_competition_id}).mappings().all()

        for row in results:
            key = f"{row['tUID_1']},{row['tUID_2']}"
            cache[key] = [row['mID'], row['mtID_1'], row['mtID_2']]

        return cache

    @staticmethod
    def _load_matches(db: Session, matches_data: list, real_competition_id: int,
                     matches_cache: dict, teams_cache: dict, comp_data: dict) -> dict:
        """Load or update matches and match teams."""
        inserted = 0
        updated = 0
        now = datetime.utcnow()

        # Get competition details
        comp_query = text("""
            SELECT realCompetitionUID, realCompetitionSYMID, realCompetitionSeasonId,
                   realCompetitionMatchDay, realCompetitionFirstMatchDay, realCompetitionLastMatchDay,
                   baseRealCompetitionID, extraRealCompetitionID
            FROM `RealCompetitions`
            WHERE realCompetitionID = :id
            LIMIT 1
        """)
        comp_result = db.execute(comp_query, {'id': real_competition_id}).first()
        if not comp_result:
            raise ValueError(f"RealCompetition {real_competition_id} not found")

        comp_uid, comp_symid, season_id, _, first_match_day, last_match_day, base_comp_id, extra_comp_id = comp_result

        for match_data in matches_data:
            if not match_data.get('team_data') or len(match_data['team_data']) < 2:
                continue

            # Get the two teams (Home and Away)
            home_team_data = next((t for t in match_data['team_data'] if t['side'] == 'Home'), None)
            away_team_data = next((t for t in match_data['team_data'] if t['side'] == 'Away'), None)

            if not (home_team_data and away_team_data):
                continue

            home_team_uid = home_team_data.get('team_ref')
            away_team_uid = away_team_data.get('team_ref')

            if not (home_team_uid and away_team_uid):
                continue

            # Build the key for cache lookup
            cache_key = f"{home_team_uid},{away_team_uid}"

            # Get team IDs from teams cache
            home_team_info = teams_cache.get(home_team_uid)
            away_team_info = teams_cache.get(away_team_uid)

            if not (home_team_info and away_team_info):
                continue

            home_team_id = home_team_info[0]
            away_team_id = away_team_info[0]

            # Parse match data
            match_date = match_data.get('date_utc')
            match_day = match_data.get('match_day')

            # Check if match exists in cache
            if cache_key in matches_cache:
                # Update existing match
                real_match_id, mt_id_home, mt_id_away = matches_cache[cache_key]

                update_query = text("""
                    UPDATE `RealMatches`
                    SET realMatchType = :match_type,
                        realMatchPeriod = :period,
                        realMatchRealPeriod = :real_period,
                        realMatchDate = :match_date,
                        realCompetitionMatchDay = :match_day,
                        lastF42Date = :now,
                        updatedIn = :now
                    WHERE realMatchID = :id
                """)
                db.execute(update_query, {
                    'id': real_match_id,
                    'match_type': match_data.get('match_type'),
                    'period': match_data.get('period'),
                    'real_period': match_data.get('period'),
                    'match_date': match_date,
                    'match_day': match_day,
                    'now': now,
                })
                updated += 1
            else:
                # Insert new match
                insert_match_query = text("""
                    INSERT INTO `RealMatches`
                    (realCompetitionID, realCompetitionUID, realCompetitionSYMID, realCompetitionSeasonId,
                     realCompetitionMatchDay, realCompetitionFirstMatchDay, realCompetitionLastMatchDay,
                     baseRealCompetitionID, extraRealCompetitionID,
                     realMatchType, realMatchPeriod, realMatchRealPeriod,
                     realMatchDate,
                     realMatchIgnore, enabled,
                     lastF42Date,
                     createdIn, updatedIn)
                    VALUES (:comp_id, :comp_uid, :comp_symid, :season_id,
                            :match_day, :first_match_day, :last_match_day,
                            :base_comp_id, :extra_comp_id,
                            :match_type, :period, :real_period,
                            :match_date,
                            :ignore, :enabled,
                            :now,
                            :now, :now)
                """)
                db.execute(insert_match_query, {
                    'comp_id': real_competition_id,
                    'comp_uid': comp_uid,
                    'comp_symid': comp_symid,
                    'season_id': season_id,
                    'match_day': match_day,
                    'first_match_day': first_match_day,
                    'last_match_day': last_match_day,
                    'base_comp_id': base_comp_id,
                    'extra_comp_id': extra_comp_id,
                    'match_type': match_data.get('match_type'),
                    'period': match_data.get('period'),
                    'real_period': match_data.get('period'),
                    'match_date': match_date,
                    'ignore': 0,
                    'enabled': 1,
                    'now': now,
                })
                db.flush()

                # Get the inserted match ID
                result = db.execute(text("""
                    SELECT realMatchID FROM `RealMatches`
                    WHERE realCompetitionID = :comp_id AND realMatchDate = :match_date
                    ORDER BY realMatchID DESC LIMIT 1
                """), {
                    'comp_id': real_competition_id,
                    'match_date': match_date,
                }).first()

                if result:
                    real_match_id = result[0]
                    inserted += 1

                    # Insert RealMatchTeams for Home and Away teams
                    for side, team_uid, team_id, team_info in [
                        ('Home', home_team_uid, home_team_id, home_team_info),
                        ('Away', away_team_uid, away_team_id, away_team_info),
                    ]:
                        real_team_number = 1 if side == 'Home' else 2

                        insert_mt_query = text("""
                            INSERT INTO `RealMatchTeams`
                            (realMatchID, realTeamID, realTeamUID, realTeamName, realTeamShortName,
                             realTeamSide, realTeamNumber,
                             createdIn, updatedIn)
                            VALUES (:match_id, :team_id, :team_uid, :team_name, :team_short_name,
                                    :side, :team_number,
                                    :now, :now)
                        """)
                        db.execute(insert_mt_query, {
                            'match_id': real_match_id,
                            'team_id': team_id,
                            'team_uid': team_uid,
                            'team_name': team_info[1],
                            'team_short_name': team_info[2],
                            'side': side,
                            'team_number': real_team_number,
                            'now': now,
                        })

        return {'inserted': inserted, 'updated': updated}
