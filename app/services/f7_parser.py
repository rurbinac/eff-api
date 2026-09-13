"""F7 OPTA XML feed parser - single match detailed results."""

import xml.etree.ElementTree as ET

from app.utils.tasks import Task


class F7Parser:
    """Parse F7 OPTA XML feeds for detailed match results."""

    _FEED = "F7"

    @staticmethod
    def parse_file(file_path: str) -> dict:
        """Parse an F7 XML file and extract structured data.

        Args:
            file_path: Path to the F7 XML file

        Returns:
            Dictionary with parsed data: task, competition, match_id, teams, players
        """
        task = Task(
            name=f"Parse {F7Parser._FEED} file: {file_path}",
            status_on_error=Task.ERROR,
        )
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            result = F7Parser._parse_root(root)
            task.add_subtask(result["task"])
        except Exception as e:
            task.add_error(f"[{type(e).__name__}]: {e!s}")
            task.close()
            raise
        task.close(status=Task.COMPLETED if not task.errors else Task.ERROR)
        result["task"] = task
        return result

    @staticmethod
    def parse_string(xml_string: str) -> dict:
        """Parse F7 XML from a string.

        Args:
            xml_string: XML content as string

        Returns:
            Dictionary with parsed data: task, competition, match_id, teams, players
        """
        task = Task(
            name=f"Parse {F7Parser._FEED} string",
            status_on_error=Task.ERROR,
        )
        try:
            root = ET.fromstring(xml_string)
            result = F7Parser._parse_root(root)
            task.add_subtask(result["task"])
        except Exception as e:
            task.add_error(f"[{type(e).__name__}]: {e!s}")
            task.close()
            raise
        task.close(status=Task.COMPLETED if not task.errors else Task.ERROR)
        result["task"] = task
        return result

    @staticmethod
    def _parse_root(root) -> dict:
        """Parse the root SoccerFeed element."""
        task = Task(name="Parse F7", status_on_error=Task.ERROR)
        task.init_info(
            "teams",
            "teams (err)",
            "players",
            "players (err)",
            "lineup",
            "goals",
            "bookings",
            "substitutions",
        )

        doc = root.find(".//SoccerDocument")
        if doc is None:
            task.add_error("No SoccerDocument found in F7 feed")
            task.close()
            raise ValueError("No SoccerDocument found in F7 feed")

        # Extract match ID from SoccerDocument uID
        match_id = doc.get("uID")

        # Parse Competition
        competition = F7Parser._parse_competition(doc)

        # Parse Match Data
        match_data = F7Parser._parse_match_data(doc)

        # Parse Teams and Players
        teams_data = {}
        players_data = {}

        for team_elem in doc.findall(".//Team"):
            team_uid = team_elem.get("uID")
            if team_uid:
                teams_data[team_uid] = F7Parser._parse_team(team_elem)
                task.inc("teams")
                # Extract players from this team
                for player_elem in team_elem.findall("Player"):
                    player = F7Parser._parse_player(player_elem, team_uid)
                    if player:
                        players_data[player["realPlayerUID"]] = player
                        task.inc("players")
                    else:
                        task.inc("players (err)")
            else:
                task.inc("teams (err)")

        # Parse PlayerLineUp data from MatchData
        player_lineup_data = F7Parser._parse_player_lineup(doc)
        match_data["player_lineup"] = player_lineup_data
        task.assign("lineup", len(player_lineup_data))

        # Parse goals from MatchData
        goals = F7Parser._parse_goals(doc)
        match_data["goals"] = goals
        task.assign("goals", len(goals))

        # Parse bookings from MatchData
        bookings = F7Parser._parse_bookings(doc)
        match_data["bookings"] = bookings
        task.assign("bookings", len(bookings))

        # Parse substitutions from MatchData
        substitutions = F7Parser._parse_substitutions(doc)
        match_data["substitutions"] = substitutions
        task.assign("substitutions", len(substitutions))

        task.close(status=Task.COMPLETED if not task.errors else Task.ERROR)
        return {
            "task": task,
            "match_id": match_id,
            "competition": competition,
            "match_data": match_data,
            "teams": teams_data,
            "players": players_data,
        }

    @staticmethod
    def _parse_competition(doc) -> dict:
        """Parse Competition element."""
        comp_elem = doc.find("Competition")
        if comp_elem is None:
            return {}

        competition = {
            "realCompetitionUID": comp_elem.get("uID"),
        }

        # Extract stats
        for stat in comp_elem.findall("Stat"):
            stat_type = stat.get("Type")
            stat_value = stat.text
            if stat_type == "symid":
                competition["realCompetitionSYMID"] = stat_value
            elif stat_type == "season_id":
                competition["realCompetitionSeasonId"] = stat_value
            elif stat_type == "matchday":
                competition["realCompetitionMatchDay"] = stat_value

        return competition

    @staticmethod
    def _parse_match_data(doc) -> dict:
        """Parse MatchData element."""
        match_elem = doc.find("MatchData")
        if match_elem is None:
            return {}

        match_info = match_elem.find("MatchInfo")

        match_data = {
            # Internal lookup fields (XML UIDs, not direct DB columns)
            "home_team_ref": None,
            "away_team_ref": None,
            "home_score": None,
            "away_score": None,
            # MatchInfo attributes → RealMatches columns
            "realMatchType": match_info.get("MatchType") if match_info is not None else None,
            "realMatchPeriod": match_info.get("Period") if match_info is not None else None,
            # MatchInfo child elements → RealMatches columns
            "realMatchAttendance": None,
            "realMatchDate": None,
            "realMatchDateOffset": None,
            "realMatchResultType": None,
            # Stats → RealMatches columns
            "realMatchTime": None,
            "realMatchFirstHalfTime": None,
            "realMatchSecondHalfTime": None,
        }

        if match_info is not None:
            attendance_elem = match_info.find("Attendance")
            if attendance_elem is not None:
                match_data["realMatchAttendance"] = attendance_elem.text

            date_elem = match_info.find("Date")
            if date_elem is not None:
                match_data["realMatchDate"] = date_elem.text
                # Extract offset from date if present (format: 20250519T200000+0100)
                if match_data["realMatchDate"] and "+" in match_data["realMatchDate"]:
                    match_data["realMatchDateOffset"] = match_data["realMatchDate"].split("+")[1]

            result_elem = match_info.find("Result")
            if result_elem is not None:
                match_data["realMatchResultType"] = result_elem.get("Type")

        # Parse Stat elements for match times
        for stat in match_elem.findall("Stat"):
            stat_type = stat.get("Type")
            stat_value = stat.text
            if stat_type == "match_time":
                match_data["realMatchTime"] = stat_value
            elif stat_type == "first_half_time":
                match_data["realMatchFirstHalfTime"] = stat_value
            elif stat_type == "second_half_time":
                match_data["realMatchSecondHalfTime"] = stat_value

        # Parse TeamData elements
        for team_data in match_elem.findall("TeamData"):
            side = team_data.get("Side")
            team_ref = team_data.get("TeamRef")
            score = team_data.get("Score")

            if side == "Home":
                match_data["home_team_ref"] = team_ref
                match_data["home_score"] = score
            elif side == "Away":
                match_data["away_team_ref"] = team_ref
                match_data["away_score"] = score

        return match_data

    @staticmethod
    def _parse_team(team_elem) -> dict:
        """Parse Team element."""
        return {
            "realTeamUID": team_elem.get("uID"),
            "realTeamName": F7Parser._get_text(team_elem, "Name"),
            "realTeamOfficialName": F7Parser._get_text(team_elem, "Official_name"),
        }

    @staticmethod
    def _parse_player(player_elem, team_uid: str) -> dict | None:
        """Parse Player element from Team."""
        uid = player_elem.get("uID")
        if not uid:
            return None

        person_name = player_elem.find("PersonName")
        first_name = None
        last_name = None
        known_name = None

        if person_name is not None:
            first_name = F7Parser._get_text(person_name, "First")
            last_name = F7Parser._get_text(person_name, "Last")
            known_name = F7Parser._get_text(person_name, "Known")

        return {
            "realPlayerUID": uid,
            "realTeamUID": team_uid,
            "position": player_elem.get("Position"),
            "firstName": first_name,
            "lastName": last_name,
            "knownName": known_name,
        }

    @staticmethod
    def _get_text(elem, tag: str) -> str | None:
        """Get text from a child element."""
        child = elem.find(tag)
        return child.text if child is not None else None

    @staticmethod
    def _parse_player_lineup(doc) -> dict:
        """Parse PlayerLineUp data from MatchData/TeamData elements."""
        lineup_data = {}

        match_elem = doc.find("MatchData")
        if match_elem is None:
            return lineup_data

        # Process each TeamData (Home and Away)
        for team_data in match_elem.findall("TeamData"):
            lineup_elem = team_data.find("PlayerLineUp")
            if lineup_elem is None:
                continue

            # Process each MatchPlayer
            for match_player in lineup_elem.findall("MatchPlayer"):
                player_ref = match_player.get("PlayerRef")
                if not player_ref:
                    continue

                lineup_data[player_ref] = {
                    "realPlayerUID": player_ref,
                    "status": match_player.get("Status"),
                    "formationPlace": match_player.get("Formation_Place"),
                    "shirtNumber": match_player.get("ShirtNumber"),
                    "position": match_player.get("Position"),
                }

        return lineup_data

    @staticmethod
    def _parse_goals(doc) -> list:
        """Parse Goal elements from MatchData/TeamData."""
        goals = []

        match_elem = doc.find("MatchData")
        if match_elem is None:
            return goals

        # Process each TeamData (Home and Away)
        for team_data in match_elem.findall("TeamData"):
            team_uid = team_data.get("TeamRef")
            if not team_uid:
                continue

            # Process each Goal
            for goal_elem in team_data.findall("Goal"):
                goals.append(
                    {
                        "team_uid": team_uid,
                        "element": goal_elem,
                    }
                )

        return goals

    @staticmethod
    def _parse_bookings(doc) -> list:
        """Parse Booking elements from MatchData/TeamData."""
        bookings = []

        match_elem = doc.find("MatchData")
        if match_elem is None:
            return bookings

        # Process each TeamData (Home and Away)
        for team_data in match_elem.findall("TeamData"):
            team_uid = team_data.get("TeamRef")
            if not team_uid:
                continue

            # Process each Booking
            for booking_elem in team_data.findall("Booking"):
                bookings.append(
                    {
                        "team_uid": team_uid,
                        "element": booking_elem,
                    }
                )

        return bookings

    @staticmethod
    def _parse_substitutions(doc) -> list:
        """Parse Substitution elements from MatchData/TeamData."""
        substitutions = []

        match_elem = doc.find("MatchData")
        if match_elem is None:
            return substitutions

        # Process each TeamData (Home and Away)
        for team_data in match_elem.findall("TeamData"):
            team_uid = team_data.get("TeamRef")
            if not team_uid:
                continue

            # Process each Substitution
            for sub_elem in team_data.findall("Substitution"):
                substitutions.append(
                    {
                        "team_uid": team_uid,
                        "element": sub_elem,
                    }
                )

        return substitutions
