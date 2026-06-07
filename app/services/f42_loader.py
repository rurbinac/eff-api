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

            # Calculate draft position order
            draft_position_order = DraftPositions.get_order(position, real_position)

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
                     draftPositionOrder,
                     isProcessedMember,
                     lastF42Date, lastFDate,
                     createdIn, updatedIn)
                    VALUES (:comp_id, :comp_uid, :comp_symid, :season_id,
                            :base_comp_id, :extra_comp_id,
                            :team_id, :team_uid,
                            :player_uid, :first_name, :last_name, :known_name,
                            :position, :real_position,
                            :birth_date, :weight, :height, :jersey_number,
                            :draft_pos_order,
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
                    'draft_pos_order': draft_position_order,
                    'is_processed': 0,
                    'now': now,
                })
                inserted += 1

        return {'inserted': inserted, 'updated': updated}
