"""F7 OPTA XML feed parser - single match detailed results."""

import xml.etree.ElementTree as ET
from typing import Optional


class F7Parser:
    """Parse F7 OPTA XML feeds for detailed match results."""

    @staticmethod
    def parse_file(file_path: str) -> dict:
        """Parse an F7 XML file and extract structured data.

        Args:
            file_path: Path to the F7 XML file

        Returns:
            Dictionary with parsed data: competition, match_id, teams, players
        """
        tree = ET.parse(file_path)
        root = tree.getroot()

        return F7Parser._parse_root(root)

    @staticmethod
    def parse_string(xml_string: str) -> dict:
        """Parse F7 XML from a string.

        Args:
            xml_string: XML content as string

        Returns:
            Dictionary with parsed data
        """
        root = ET.fromstring(xml_string)
        return F7Parser._parse_root(root)

    @staticmethod
    def _parse_root(root) -> dict:
        """Parse the root SoccerFeed element."""
        doc = root.find('.//SoccerDocument')
        if doc is None:
            raise ValueError("No SoccerDocument found in F7 feed")

        # Extract match ID from SoccerDocument uID
        match_id = doc.get('uID')

        # Parse Competition
        competition = F7Parser._parse_competition(doc)

        # Parse Match Data
        match_data = F7Parser._parse_match_data(doc)

        # Parse Teams and Players
        teams_data = {}
        players_data = {}

        for team_elem in doc.findall('.//Team'):
            team_uid = team_elem.get('uID')
            if team_uid:
                teams_data[team_uid] = F7Parser._parse_team(team_elem)
                # Extract players from this team
                for player_elem in team_elem.findall('Player'):
                    player = F7Parser._parse_player(player_elem, team_uid)
                    if player:
                        players_data[player['realPlayerUID']] = player

        # Parse PlayerLineUp data from MatchData
        player_lineup_data = F7Parser._parse_player_lineup(doc)
        match_data['player_lineup'] = player_lineup_data

        # Parse goals from MatchData
        goals = F7Parser._parse_goals(doc)
        match_data['goals'] = goals

        # Parse bookings from MatchData
        bookings = F7Parser._parse_bookings(doc)
        match_data['bookings'] = bookings

        # Parse substitutions from MatchData
        substitutions = F7Parser._parse_substitutions(doc)
        match_data['substitutions'] = substitutions

        return {
            'match_id': match_id,
            'competition': competition,
            'match_data': match_data,
            'teams': teams_data,
            'players': players_data,
        }

    @staticmethod
    def _parse_competition(doc) -> dict:
        """Parse Competition element."""
        comp_elem = doc.find('Competition')
        if comp_elem is None:
            return {}

        competition = {
            'uID': comp_elem.get('uID'),
        }

        # Extract stats
        for stat in comp_elem.findall('Stat'):
            stat_type = stat.get('Type')
            stat_value = stat.text
            if stat_type == 'symid':
                competition['symid'] = stat_value
            elif stat_type == 'season_id':
                competition['season_id'] = stat_value
            elif stat_type == 'matchday':
                competition['matchday'] = stat_value

        return competition

    @staticmethod
    def _parse_match_data(doc) -> dict:
        """Parse MatchData element."""
        match_elem = doc.find('MatchData')
        if match_elem is None:
            return {}

        match_info = match_elem.find('MatchInfo')

        match_data = {
            'home_team_ref': None,
            'away_team_ref': None,
            'home_score': None,
            'away_score': None,
            'home_side': 'Home',
            'away_side': 'Away',
            # MatchInfo attributes
            'match_type': match_info.get('MatchType') if match_info is not None else None,
            'period': match_info.get('Period') if match_info is not None else None,
            # MatchInfo child elements
            'attendance': None,
            'date': None,
            'date_offset': None,
            'result_type': None,
            # Stats
            'match_time': None,
            'first_half_time': None,
            'second_half_time': None,
        }

        if match_info is not None:
            # Parse MatchInfo children
            attendance_elem = match_info.find('Attendance')
            if attendance_elem is not None:
                match_data['attendance'] = attendance_elem.text

            date_elem = match_info.find('Date')
            if date_elem is not None:
                match_data['date'] = date_elem.text
                # Extract offset from date if present (format: 20250519T200000+0100)
                if match_data['date'] and '+' in match_data['date']:
                    match_data['date_offset'] = match_data['date'].split('+')[1]

            result_elem = match_info.find('Result')
            if result_elem is not None:
                match_data['result_type'] = result_elem.get('Type')

        # Parse Stat elements for match times
        for stat in match_elem.findall('Stat'):
            stat_type = stat.get('Type')
            stat_value = stat.text
            if stat_type == 'match_time':
                match_data['match_time'] = stat_value
            elif stat_type == 'first_half_time':
                match_data['first_half_time'] = stat_value
            elif stat_type == 'second_half_time':
                match_data['second_half_time'] = stat_value

        # Parse TeamData elements
        for team_data in match_elem.findall('TeamData'):
            side = team_data.get('Side')
            team_ref = team_data.get('TeamRef')
            score = team_data.get('Score')

            if side == 'Home':
                match_data['home_team_ref'] = team_ref
                match_data['home_score'] = score
            elif side == 'Away':
                match_data['away_team_ref'] = team_ref
                match_data['away_score'] = score

        return match_data

    @staticmethod
    def _parse_team(team_elem) -> dict:
        """Parse Team element."""
        return {
            'uID': team_elem.get('uID'),
            'name': F7Parser._get_text(team_elem, 'Name'),
            'official_name': F7Parser._get_text(team_elem, 'Official_name'),
        }

    @staticmethod
    def _parse_player(player_elem, team_uid: str) -> Optional[dict]:
        """Parse Player element from Team."""
        uid = player_elem.get('uID')
        if not uid:
            return None

        person_name = player_elem.find('PersonName')
        first_name = None
        last_name = None
        known_name = None

        if person_name is not None:
            first_name = F7Parser._get_text(person_name, 'First')
            last_name = F7Parser._get_text(person_name, 'Last')
            known_name = F7Parser._get_text(person_name, 'Known')

        return {
            'realPlayerUID': uid,
            'realTeamUID': team_uid,
            'position': player_elem.get('Position'),
            'firstName': first_name,
            'lastName': last_name,
            'knownName': known_name,
        }

    @staticmethod
    def _get_text(elem, tag: str) -> Optional[str]:
        """Get text from a child element."""
        child = elem.find(tag)
        return child.text if child is not None else None

    @staticmethod
    def _parse_player_lineup(doc) -> dict:
        """Parse PlayerLineUp data from MatchData/TeamData elements."""
        lineup_data = {}

        match_elem = doc.find('MatchData')
        if match_elem is None:
            return lineup_data

        # Process each TeamData (Home and Away)
        for team_data in match_elem.findall('TeamData'):
            lineup_elem = team_data.find('PlayerLineUp')
            if lineup_elem is None:
                continue

            # Process each MatchPlayer
            for match_player in lineup_elem.findall('MatchPlayer'):
                player_ref = match_player.get('PlayerRef')
                if not player_ref:
                    continue

                lineup_data[player_ref] = {
                    'playerRef': player_ref,
                    'status': match_player.get('Status'),
                    'formation_place': match_player.get('Formation_Place'),
                    'shirt_number': match_player.get('ShirtNumber'),
                    'position': match_player.get('Position'),
                }

        return lineup_data

    @staticmethod
    def _parse_goals(doc) -> list:
        """Parse Goal elements from MatchData/TeamData."""
        goals = []

        match_elem = doc.find('MatchData')
        if match_elem is None:
            return goals

        # Process each TeamData (Home and Away)
        for team_data in match_elem.findall('TeamData'):
            team_uid = team_data.get('TeamRef')
            if not team_uid:
                continue

            # Process each Goal
            for goal_elem in team_data.findall('Goal'):
                goals.append({
                    'team_uid': team_uid,
                    'element': goal_elem,
                })

        return goals

    @staticmethod
    def _parse_bookings(doc) -> list:
        """Parse Booking elements from MatchData/TeamData."""
        bookings = []

        match_elem = doc.find('MatchData')
        if match_elem is None:
            return bookings

        # Process each TeamData (Home and Away)
        for team_data in match_elem.findall('TeamData'):
            team_uid = team_data.get('TeamRef')
            if not team_uid:
                continue

            # Process each Booking
            for booking_elem in team_data.findall('Booking'):
                bookings.append({
                    'team_uid': team_uid,
                    'element': booking_elem,
                })

        return bookings

    @staticmethod
    def _parse_substitutions(doc) -> list:
        """Parse Substitution elements from MatchData/TeamData."""
        substitutions = []

        match_elem = doc.find('MatchData')
        if match_elem is None:
            return substitutions

        # Process each TeamData (Home and Away)
        for team_data in match_elem.findall('TeamData'):
            team_uid = team_data.get('TeamRef')
            if not team_uid:
                continue

            # Process each Substitution
            for sub_elem in team_data.findall('Substitution'):
                substitutions.append({
                    'team_uid': team_uid,
                    'element': sub_elem,
                })

        return substitutions
