"""F42 OPTA XML feed parser."""

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional


class F42Parser:
    """Parse F42 OPTA XML feeds."""

    @staticmethod
    def parse_file(file_path: str) -> dict:
        """Parse an F42 XML file and extract structured data.

        Args:
            file_path: Path to the F42 XML file

        Returns:
            Dictionary with parsed data: competitions, teams, players, matches
        """
        tree = ET.parse(file_path)
        root = tree.getroot()

        return F42Parser._parse_root(root)

    @staticmethod
    def parse_string(xml_string: str) -> dict:
        """Parse F42 XML from a string.

        Args:
            xml_string: XML content as string

        Returns:
            Dictionary with parsed data
        """
        root = ET.fromstring(xml_string)
        return F42Parser._parse_root(root)

    @staticmethod
    def _parse_root(root) -> dict:
        """Parse the root SoccerFeed element."""
        doc = root.find('.//SoccerDocument')
        if doc is None:
            raise ValueError("No SoccerDocument found in F42 feed")

        competition = {
            'competition_code': doc.get('competition_code'),
            'competition_id': doc.get('competition_id'),
            'competition_name': doc.get('competition_name'),
            'season_id': doc.get('season_id'),
            'season_name': doc.get('season_name'),
            'game_system_id': doc.get('game_system_id'),
            'timestamp': doc.get('timestamp'),
        }

        # Derive competition country from code (default to England for now)
        comp_code = competition.get('competition_code', 'EN_PR')
        if comp_code.startswith('EN_'):
            competition['country'] = 'England'
        else:
            competition['country'] = 'England'  # Default for now

        # Parse Squads for teams and players
        squads = root.find('.//Squads')
        teams = []
        players = []
        if squads is not None:
            teams, players = F42Parser._parse_squads(squads)

        # Parse MatchData
        matches = []
        for match_data in root.findall('.//MatchData'):
            match = F42Parser._parse_match_data(match_data)
            if match:
                matches.append(match)

        return {
            'competition': competition,
            'teams': teams,
            'players': players,
            'matches': matches,
        }

    @staticmethod
    def _parse_squads(squads_elem) -> tuple[list, list]:
        """Parse Teams and Players from Squads element."""
        teams = []
        players = []

        for team_elem in squads_elem.findall('.//Team'):
            team = F42Parser._parse_team(team_elem)
            if team:
                teams.append(team)

            # Parse players within this team
            for player_elem in team_elem.findall('.//Player'):
                player = F42Parser._parse_player(player_elem, team['uID'])
                if player:
                    players.append(player)

        return teams, players

    @staticmethod
    def _parse_team(team_elem) -> Optional[dict]:
        """Parse a Team element from Squads."""
        uid = team_elem.get('uID')
        if not uid:
            return None

        name_elem = team_elem.find('Name')
        symid_elem = team_elem.find('SYMID')

        return {
            'uID': uid,
            'name': name_elem.text if name_elem is not None else None,
            'symid': symid_elem.text if symid_elem is not None else None,
        }

    @staticmethod
    def _parse_player(player_elem, team_uid: str) -> Optional[dict]:
        """Parse a Player element from Team."""
        uid = player_elem.get('uID')
        if not uid:
            return None

        return {
            'uID': uid,
            'team_uID': team_uid,
            'name': player_elem.get('Name'),
            'position': player_elem.get('Position'),
            'shirt_number': player_elem.get('ShirtNumber'),
            'status': player_elem.get('Status'),
        }

    @staticmethod
    def _parse_match_data(match_elem) -> Optional[dict]:
        """Parse a MatchData element."""
        uid = match_elem.get('uID')
        if not uid:
            return None

        match_info = match_elem.find('MatchInfo')
        if match_info is None:
            return None

        match = {
            'uID': uid,
            'match_day': match_info.get('MatchDay'),
            'match_type': match_info.get('MatchType'),
            'period': match_info.get('Period'),
            'var': match_info.get('Var'),
        }

        # Parse date/time
        date_elem = match_elem.find('MatchInfo/Date')
        date_utc_elem = match_elem.find('MatchInfo/DateUtc')
        if date_elem is not None:
            match['date'] = date_elem.text
        if date_utc_elem is not None:
            match['date_utc'] = date_utc_elem.text

        # Parse venue and attendance
        for stat in match_elem.findall('Stat'):
            stat_type = stat.get('Type')
            if stat_type == 'Venue':
                match['venue'] = stat.text
            elif stat_type == 'Attendance':
                match['attendance'] = stat.text

        # Parse team data (goals, bookings, scores)
        team_data_list = []
        for team_data in match_elem.findall('TeamData'):
            team_info = F42Parser._parse_team_data(team_data)
            if team_info:
                team_data_list.append(team_info)

        match['team_data'] = team_data_list

        return match

    @staticmethod
    def _parse_team_data(team_elem) -> Optional[dict]:
        """Parse TeamData element from MatchData."""
        side = team_elem.get('Side')
        team_ref = team_elem.get('TeamRef')
        score = team_elem.get('Score')
        half_time_score = team_elem.get('HalfTimeScore')

        if not (side and team_ref):
            return None

        team_data = {
            'side': side,
            'team_ref': team_ref,
            'score': score,
            'half_time_score': half_time_score,
            'goals': [],
            'bookings': [],
        }

        # Parse goals
        for goal in team_elem.findall('Goal'):
            goal_info = {
                'player_ref': goal.get('PlayerRef'),
                'time': goal.get('Time'),
                'period': goal.get('Period'),
                'type': goal.get('Type'),
            }
            team_data['goals'].append(goal_info)

        # Parse bookings
        for booking in team_elem.findall('Booking'):
            booking_info = {
                'player_ref': booking.get('PlayerRef'),
                'card': booking.get('Card'),
                'card_type': booking.get('CardType'),
                'period': booking.get('Period'),
                'time': booking.get('Time'),
                'reason': booking.get('Reason'),
            }
            team_data['bookings'].append(booking_info)

        return team_data
