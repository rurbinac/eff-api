"""F42 OPTA XML feed parser using streaming (iterparse) for memory efficiency."""

import xml.etree.ElementTree as ET
from datetime import datetime

from app.constants import RealCompetitionConstants
from app.services.services_exception import FeedParsingException
from app.utils.dt import utc_lowest


class F42Parser:
    """Parse F42 OPTA XML feeds using two-pass streaming approach.

    Pass 1: Parse Squads (competitions, teams, players) - minimal memory
    Pass 2: Parse MatchData (matches) - uses team mappings from Pass 1
    """

    _FEED = "F42"

    @staticmethod
    def parse_file(file_path: str) -> dict:
        """Parse an F42 XML file in two passes for memory efficiency.

        Args:
            file_path: Path to the F42 XML file

        Returns:
            Dictionary with parsed data: competition, teams, players, matches
        """
        # Pass 1: Extract competition info and Squads (teams, players)
        competition, teams, players, team_id_mapping = F42Parser._parse_pass_1_squads(
            file_path
        )

        # Pass 2: Extract MatchData (using team mappings from Pass 1)
        matches = F42Parser._parse_pass_2_matches(file_path, team_id_mapping)

        return {
            "competition": competition,
            "teams": teams,
            "players": players,
            "matches": matches,
        }

    @staticmethod
    def _parse_pass_1_squads(
        file_path: str,
    ) -> tuple[dict, list[dict], list[dict], dict]:
        """Pass 1: Stream through XML and extract Squads (teams and players).

        Returns:
            (competition, teams, players, team_id_mapping)
            team_id_mapping: dict mapping team uID to team data for Pass 2
        """
        competition = None
        teams = []
        players = []
        team_id_mapping = {}  # Store team uID -> team data for Pass 2
        in_squads = None

        # Use iterparse for memory-efficient streaming
        context = ET.iterparse(file_path, events=["start", "end"])

        for event, elem in context:
            # Get competition info from SoccerDocument (start event)
            if (
                event == "start"
                and elem.tag == "SoccerDocument"
                and competition is None
            ):
                competition = F42Parser._parse_competition_element(elem)
            # Track when we enter/exit Squads section
            elif event == "start" and elem.tag == "Squads":
                in_squads = True

            # Process Team elements while in Squads (end event after all children parsed)
            elif event == "end" and elem.tag == "Team" and in_squads:
                team = F42Parser._parse_team_element(elem)
                if team:
                    teams.append(team)
                    team_id_mapping[team["uID"]] = team

                    # Parse players within this team (from already-parsed element)
                    for player_elem in elem.findall("Player"):
                        player = F42Parser._parse_player_element(
                            player_elem, team["uID"]
                        )
                        if player:
                            players.append(player)

                # Clear element to save memory
                elem.clear()

            # Stop after Squads section (MatchData is in Pass 2)
            elif event == "end" and elem.tag == "Squads":
                in_squads = False
                break

        if competition is None:
            competition = {}

        if not competition.get("competition_code"):
            raise FeedParsingException(F42Parser._FEED, "Missing competition_code")
        elif competition["competition_code"] not in (
            RealCompetitionConstants.BASE_SYMID,
            RealCompetitionConstants.EXTRA_SYMID,
        ):
            raise FeedParsingException(
                F42Parser._FEED,
                f"Invalid competition_code: '{competition['competition_code']}'",
            )
        if not competition.get("season_id"):
            raise FeedParsingException(F42Parser._FEED, "Missing season_id")
        if in_squads is None:
            raise FeedParsingException(F42Parser._FEED, "Missing Squads section")
        if len(teams) == 0:
            raise FeedParsingException(F42Parser._FEED, "No teams found")
        if len(players) == 0:
            raise FeedParsingException(F42Parser._FEED, "No players found")

        return competition, teams, players, team_id_mapping

    @staticmethod
    def _parse_pass_2_matches(file_path: str, team_id_mapping: dict) -> list[dict]:
        """Pass 2: Stream through XML and extract MatchData only.

        Args:
            file_path: Path to the F42 XML file
            team_id_mapping: Team uID mapping from Pass 1

        Returns:
            List of match dictionaries
        """
        matches = []

        # Use iterparse for memory-efficient streaming
        context = ET.iterparse(file_path, events=["end"])

        for event, elem in context:
            # Process MatchData elements (end event after all children parsed)
            if event == "end" and elem.tag == "MatchData":
                match = F42Parser._parse_match_element(elem, team_id_mapping)
                if match:
                    matches.append(match)

                # Clear element to save memory
                elem.clear()

        if len(matches) == 0:
            raise FeedParsingException(F42Parser._FEED, "No matches found")
        return matches

    @staticmethod
    def _parse_competition_element(competition_elem) -> dict:
        """Parses the competition data from SoccerDocument

        Args:
            competition_elem: The XML node

        Returns:
            dict | None: The parsed competition data
        """
        return {
            "competition_code": competition_elem.get("competition_code"),
            "competition_name": competition_elem.get("competition_name"),
            "season_id": competition_elem.get("season_id"),
            "timestamp": F42Parser._parse_feed_timestamp(
                competition_elem.get("timestamp")
            ),
        }

    @staticmethod
    def _parse_team_element(team_elem) -> dict | None:
        """Parses a Team element from Squads

        Args:
            team_elem: The XML node

        Returns:
            dict | None: The parsed team data
        """
        uid = team_elem.get("uID")
        if not uid:
            return None

        name_elem = team_elem.find("Name")
        symid_elem = team_elem.find("SYMID")

        return {
            "uID": uid,
            "name": name_elem.text if name_elem is not None else None,
            "symid": symid_elem.text if symid_elem is not None else None,
        }

    @staticmethod
    def _parse_player_element(player_elem, team_uid: str) -> dict | None:
        """Parses a Player element from Team

        Args:
            player_elem: The XML node
            team_uid: The UID of the team to which the player belongs

        Returns:
            dict | None: The parsed player data
        """
        uid = player_elem.get("uID")
        if not uid:
            return None

        name_elem = player_elem.find("Name")
        position_elem = player_elem.find("Position")
        player = {
            "uID": uid,
            "team_uID": team_uid,
            "name": name_elem.text if name_elem is not None else None,
            "position": position_elem.text if position_elem is not None else None,
            "shirt_number": player_elem.get("ShirtNumber"),
            "status": player_elem.get("Status"),
        }

        # Extract player stats from Stat elements
        stat_map = {
            "first_name": "first_name",
            "last_name": "last_name",
            "known_name": "known_name",
            "real_position": "real_position",
            "birth_date": "birth_date",
            "weight": "weight",
            "height": "height",
            "jersey_num": "jersey_number",
        }

        for stat_elem in player_elem.findall("Stat"):
            stat_type = stat_elem.get("Type")
            stat_value = stat_elem.text
            if stat_type in stat_map:
                player[stat_map[stat_type]] = stat_value

        return player

    @staticmethod
    def _parse_match_element(match_elem, team_id_mapping: dict) -> dict | None:
        """Parses a MatchData element from SoccerDocument

        Args:
            match_elem: The XML node
            team_id_mapping: A dictionary mapping team UIDs to their data

        Returns:
            dict | None: The parsed match data
        """
        uid = match_elem.get("uID")
        if not uid:
            return None

        match_info = match_elem.find("MatchInfo")
        if match_info is None:
            return None

        match = {
            "uID": uid,
            "match_day": match_info.get("MatchDay"),
            "match_type": match_info.get("MatchType"),
            "period": match_info.get("Period"),
            "var": match_info.get("Var"),
        }

        # Parse date/time
        date_elem = match_elem.find("MatchInfo/Date")
        date_utc_elem = match_elem.find("MatchInfo/DateUtc")
        if date_elem is not None:
            match["date"] = date_elem.text
        if date_utc_elem is not None:
            match["date_utc"] = date_utc_elem.text

        # Parse venue and attendance
        for stat in match_elem.findall("Stat"):
            stat_type = stat.get("Type")
            if stat_type == "Venue":
                match["venue"] = stat.text
            elif stat_type == "Attendance":
                match["attendance"] = stat.text

        # Parse team data (goals, bookings, scores)
        team_data_list = []
        for team_data_elem in match_elem.findall("TeamData"):
            team_info = F42Parser._parse_team_data_element(
                team_data_elem, team_id_mapping
            )
            if team_info:
                team_data_list.append(team_info)

        match["team_data"] = team_data_list

        return match

    @staticmethod
    def _parse_team_data_element(team_elem, team_id_mapping: dict) -> dict | None:
        """Parses a TeamData element from MatchData

        Args:
            team_elem: The XML node
            team_id_mapping: A dictionary mapping team UIDs to their data

        Returns:
            dict | None: The parsed team data
        """
        side = team_elem.get("Side")
        team_ref = team_elem.get("TeamRef")
        score = team_elem.get("Score")
        half_time_score = team_elem.get("HalfTimeScore")

        if not (side and team_ref):
            return None

        team_data = {
            "side": side,
            "team_ref": team_ref,
            "score": score,
            "half_time_score": half_time_score,
            "goals": [],
            "bookings": [],
        }

        # Parse goals
        for goal in team_elem.findall("Goal"):
            goal_info = {
                "player_ref": goal.get("PlayerRef"),
                "time": goal.get("Time"),
                "period": goal.get("Period"),
                "type": goal.get("Type"),
            }
            team_data["goals"].append(goal_info)

        # Parse bookings
        for booking in team_elem.findall("Booking"):
            booking_info = {
                "player_ref": booking.get("PlayerRef"),
                "card": booking.get("Card"),
                "card_type": booking.get("CardType"),
                "period": booking.get("Period"),
                "time": booking.get("Time"),
                "reason": booking.get("Reason"),
            }
            team_data["bookings"].append(booking_info)

        return team_data

    @staticmethod
    def _parse_feed_timestamp(raw: str | None) -> datetime:
        """Parse the SoccerDocument timestamp attribute (e.g. '20260809T080049Z')."""
        if not raw:
            return utc_lowest()
        try:
            return datetime.strptime(raw, "%Y%m%dT%H%M%SZ")
        except ValueError:
            return utc_lowest()
