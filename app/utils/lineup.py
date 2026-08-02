import re
from collections.abc import Iterator
from typing import Any, ClassVar, Final

from sqlalchemy import text
from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session

from app.constants import (
    CompetitionTypeConstants,
    DraftPositionConstants,
    LineupConstants,
    MatchStatusConstants,
    RealMatchStatus,
)
from app.utils.member_keys import GetKeyData, GroupData, MKeys, PackedData


class Formations:
    """
    Handles validation and management of football formations.

    This class validates formation strings (e.g., "442", "433") and provides
    functionality to check if a given set of player positions can form a valid
    formation based on position distribution (GK, DEF, MID, STR).
    """

    _valid_formations: ClassVar[dict[str, dict[str, int]]] = {}
    """Class variable storing valid formations with their position requirements."""

    FORMATION_CNT: Final[int] = 12
    """Total number of players in a formation including goalkeeper and team slot."""

    @staticmethod
    def load_valid_formations(txt: str) -> None:
        """
        Load valid formations from a comma-separated string.

        Args:
            txt: Comma-separated string of formation numbers (e.g., "442,433,451")

        The method validates each formation by:
        1. Ensuring it's a 3-digit number
        2. Checking that digits sum to 10 (for outfield players)
        3. Storing the position distribution (GK:1, DEF:first digit, MID:second digit, STR:third digit, TEAM:1)
        """
        for vf in txt.replace(" ", "").split(","):
            # Validate formation format (e.g., "442", "433", "451")
            if re.match(r"^[1-9][1-9][1-9]$", vf):
                # Validate that digits sum to 10 (total players minus GK and TEAM slots)
                if sum(int(d) for d in vf) != Formations.FORMATION_CNT - 2:
                    print(f"Warning: Formation {vf} doesn't sum to 10")
                    continue
                if vf not in Formations._valid_formations:
                    Formations._valid_formations[vf] = {
                        DraftPositionConstants.GOALKEEPER: 1,
                        DraftPositionConstants.DEFENDER: int(vf[0]),
                        DraftPositionConstants.MIDFIELDER: int(vf[1]),
                        DraftPositionConstants.STRIKER: int(vf[2]),
                        DraftPositionConstants.EPL_TEAM: 1,
                    }

    @staticmethod
    def formation_found(
        dp_count: dict[str, int], dp_to_add: str | None = None
    ) -> tuple[bool, str | None, dict[str, int]]:
        """
        Check if adding a player position results in a valid formation.

        Args:
            dp_count: Current count of players by draft position
            dp_to_add: Draft position to add (if any)

        Returns:
            tuple containing:
                - bool: True if a valid formation can be formed
                - str | None: Name of the formation if complete, None otherwise
                - dict[str, int]: Updated position counts
        """
        # Initialize position counts if adding and empty
        if dp_to_add and not dp_count:
            dp_count = dict.fromkeys(
                next(iter(Formations._valid_formations.values())), 0
            )
        # Clear invalid position to add
        if dp_to_add and dp_to_add not in dp_count:
            dp_to_add = None

        # Check each valid formation
        for formation_name, dp_count_max in Formations._valid_formations.items():
            total_count = 0
            valid = True
            for dp in dp_count:
                delta = 1 if dp_to_add and dp_to_add == dp else 0
                if dp_count_max.get(dp, 0) >= dp_count[dp] + delta:
                    total_count += dp_count[dp] + delta
                else:
                    valid = False
                    break

            if valid:
                # Apply the addition if we're adding a position
                if dp_to_add is not None:
                    dp_count[dp_to_add] += 1
                return (
                    True,
                    formation_name if total_count == Formations.FORMATION_CNT else None,
                    dp_count,
                )

        return False, None, dp_count


# Load valid formations from constants
Formations.load_valid_formations(LineupConstants.VALID_FORMATIONS)


class Lineup(MKeys):
    """
    Manages football lineup data including players, teams, and substitutions.

    This class extends MKeys to handle lineup-specific operations including:
    - Cleaning and reorganizing lineup strings
    - Validating formations
    - Managing substitutions
    - Loading lineup data from database
    """

    FLAG: Final[str] = "!"
    """Flag character used to mark substituted players in the lineup string."""

    @staticmethod
    def from_ids(
        team_ids: int | list[int] | None,
        player_ids: int | list[int] | None,
        sub_player_ids: int | list[int] | None,
    ) -> str | None:
        """
        Create a lineup string from team and player IDs.

        Args:
            team_ids: Team ID(s) - first team goes to group 0, second to group 2
            player_ids: Player ID(s) for the starting lineup
            sub_player_ids: Player ID(s) for substitutes

        Returns:
            Formatted lineup string or None if any input is None
        """
        t_ids = MKeys.from_team_ids(team_ids)
        p_ids = MKeys.from_player_ids(player_ids)
        s_ids = MKeys.from_player_ids(sub_player_ids)
        if t_ids is not None and p_ids is not None and s_ids is not None:
            if t_ids:
                # Split teams into first (group 0) and second (group 2)
                t_0, t_1 = t_ids.split(MKeys.SUFFIX, 1)
                t_0 += MKeys.SUFFIX
            else:
                t_0, t_1 = "", ""
            # Format: players + first team | substitutes | second team
            return p_ids + t_0 + MKeys.DELIM + s_ids + MKeys.DELIM + t_1
        return None

    @staticmethod
    def is_empty(value: str | list | MKeys | None) -> bool:
        """
        Check if a lineup value is empty or contains no meaningful data.

        Args:
            value: The value to check (string, list, MKeys, or None)

        Returns:
            True if empty, False otherwise
        """
        if value is None:
            return True
        elif isinstance(value, MKeys):
            return len(value) == 0 and value.size == 3
        elif isinstance(value, list):
            if len(value) == 0:
                return True
            if len(value) != 3:
                return False
            for keys in value:
                if keys is None:
                    continue
                if isinstance(keys, str):
                    if keys.strip() != "":
                        return False
                elif not isinstance(keys, list) or len(keys) > 0:
                    return False
            return True
        elif isinstance(value, str):
            return value == "" or value == MKeys.DELIM * 2
        else:
            return False

    @staticmethod
    def clean_up(lineup_txt: str | None) -> str | None:
        """
        Clean and reorganize a lineup text string by categorizing items into teams.

        The input format expects a string with items separated by DELIM, where each item
        ends with SUFFIX. Items are categorized as PLAYER or TEAM and distributed across
        three output groups: team 0 players, team 1 players, and team 2 (other teams).

        Args:
            lineup_txt: A string containing lineup data with DELIM-separated items,
                       or None if no lineup exists.

        Returns:
            - If input is empty/None: Returns DELIM * 2 (two delimiters)
            - If input has wrong number of delimiters: Returns None
            - If any item doesn't end with SUFFIX: Returns None
            - If any prefix is unrecognized: Returns None
            - Otherwise: Returns a reorganized string with three DELIM-separated groups:
                group 0: PLAYER items and (at most) one TEAM from first input group
                group 1: PLAYER items from second input group
                group 2: TEAM items (from first group goes here, subsequent teams also)
        """
        # Handle empty input
        if Lineup.is_empty(lineup_txt):
            return MKeys.DELIM * 2
        # Validate delimiter count (should be exactly 3 groups)
        if lineup_txt.count(MKeys.DELIM) != 2:
            return None

        first_team = True
        txt: list[str] = ["", "", ""]

        for i, t in enumerate(lineup_txt.split(MKeys.DELIM)):
            if t == "":
                continue
            # Each item must end with SUFFIX
            if not t.endswith(MKeys.SUFFIX):
                return None

            for k in t[:-1].split(MKeys.SUFFIX):
                prefix, _ = MKeys.split_key(k)
                match prefix:
                    case MKeys.PLAYER:
                        # Players go to group 0 or 1 based on source group
                        n = 0 if i == 0 else 1
                    case MKeys.TEAM:
                        # First team goes to group 0, subsequent teams to group 2
                        n = 0 if i == 0 and first_team else 2
                        first_team = False
                    case _:
                        return None
                # Add the processed item to the appropriate bucket (with SUFFIX)
                txt[n] += k + MKeys.SUFFIX

        # Return the reorganized string with three DELIM-separated groups
        return MKeys.DELIM.join(txt)

    def __init__(self, db: Session, get_key_data: GetKeyData):
        """
        Initialize the Lineup instance.

        Args:
            db: SQLAlchemy database session
            get_key_data: Function to retrieve data about a key
        """
        super().__init__(False)
        self._db = db
        self._get_key_data = get_key_data
        self._substitutes: list[str] = []
        self._team_members: GroupData = []
        # Core lineup data
        self._match_team_id: int | None = None
        self._match_id: int | None = None
        self._team_id: int | None = None
        self._user_id: int | None = None
        self._db_lineup: str | None = None
        self._match_team_num: int | None = None
        self._real_competition_id: int | None = None
        self._real_competition_match_day: int | None = None
        self._competition_type: int | None = None
        self._competition_match_day: int | None = None
        self._match_day_map_key: str | None = None
        self._chosen_match_status: int | None = None
        self._db_match_status: int | None = None
        self._lineup_txt: str = MKeys.DELIM * 2

    @property
    def match_team_id(self) -> int | None:
        """Get the match team ID."""
        return self._match_team_id

    @property
    def match_id(self) -> int | None:
        """Get the match ID."""
        return self._match_id

    @property
    def team_id(self) -> int | None:
        """Get the team ID."""
        return self._team_id

    @property
    def user_id(self) -> int | None:
        """Get the user ID."""
        return self._user_id

    @property
    def match_team_num(self) -> int | None:
        """Get the match team num."""
        return self._match_team_num

    @property
    def real_competition_id(self) -> int | None:
        """Get the real competition id."""
        return self._real_competition_id

    @property
    def real_competition_match_day(self) -> int | None:
        """Get the real competition match day."""
        return self._real_competition_match_day

    @property
    def competition_type(self) -> int | None:
        """Get the competition type."""
        return self._competition_type

    @property
    def competition_match_day(self) -> int | None:
        """Get the competition match day."""
        return self._competition_match_day

    @property
    def match_day_map_key(self) -> str | None:
        return self._match_day_map_key

    @property
    def lineup_changed(self) -> bool:
        """Checks if the lineup has changed (compared to what is in the db)."""
        return self.pack() != self._lineup_txt

    @property
    def match_status(self) -> int | None:
        """
        Get the match status, preferring chosen status over database status.

        Returns:
            The chosen match status if set, otherwise the database match status
        """
        return (
            self._chosen_match_status
            if self._chosen_match_status is not None
            else self._db_match_status
        )

    @property
    def chosen_match_status(self) -> int | None:
        """Get the chosen match status (overrides database status)."""
        return self._chosen_match_status

    @property
    def db_match_status(self) -> int | None:
        """Get the database match status."""
        return self._db_match_status

    def read_by_match_team(self, match_team_id: int) -> RowMapping | None:
        """
        Read MatchTeam (+Match+Team) data by match team ID.

        Args:
            match_team_id: ID of the match team

        Returns:
            A RowMapping object if successfully, None otherwise
        """
        sql = """
              SELECT `mt`.`matchTeamID`,
                     `mt`.`matchID`,
                     `mt`.`userID`,
                     `mt`.`teamID`,
                     `mt`.`matchTeamNum`,
                     `mt`.`realCompetitionID`,
                     `mt`.`realCompetitionMatchDay`,
                     `m`.`realCompetitionMatchDaySort`,
                     `m`.`matchStatus`,
                     `m`.`competitionType`,
                     `m`.`competitionMatchDay`,
                     `mt`.`matchDayMapKey`,
                     `mt`.`lineup`,
                     `t`.`teamMembers`
                 FROM `MatchTeams` `mt`
                 INNER JOIN `Matches` `m` ON `m`.`matchID` = `mt`.`matchID`
                 LEFT OUTER JOIN `Teams` `t` ON `t`.`teamID` = `mt`.`teamID`
                 WHERE `mt`.`matchTeamID` = :matchTeamID
            """
        return (
            self._db.execute(text(sql), {"matchTeamID": match_team_id})
            .mappings()
            .first()
        )

    def read_by_team_id(
        self,
        team_id: int,
        competition_type: int,
        competition_match_day: int,
    ) -> RowMapping | None:
        """
        Read MatchTeam (+Match+Team) data by team ID, competition type, and match day.

        Args:
            team_id: ID of the team
            competition_type: Type of competition
            competition_match_day: Match day in the competition

        Returns:
            A RowMapping object if successfully, None otherwise
        """
        sql = """
              SELECT `mt`.`matchTeamID`,
                     `mt`.`matchID`,
                     `mt`.`userID`,
                     `mt`.`teamID`,
                     `mt`.`matchTeamNum`,
                     `mt`.`realCompetitionID`,
                     `mt`.`realCompetitionMatchDay`,
                     `m`.`matchStatus`,
                     `m`.`competitionType`,
                     `m`.`competitionMatchDay`,
                     `mt`.`matchDayMapKey`,
                     `mt`.`lineup`,
                     `t`.`teamMembers`
                 FROM `MatchTeams` `mt`
                 INNER JOIN `Matches` `m` ON `m`.`matchID` = `mt`.`matchID`
                 LEFT OUTER JOIN `Teams` `t` ON `t`.`teamID` = `mt`.`teamID`
                 WHERE `mt`.`teamID` = :teamID
                   AND `m`.`competitionType` = :competitionType
                   AND `m`.`competitionMatchDay` = :competitionMatchDay
            """
        return (
            self._db.execute(
                text(sql),
                {
                    "teamID": team_id,
                    "competitionType": competition_type,
                    "competitionMatchDay": competition_match_day,
                },
            )
            .mappings()
            .first()
        )

    def load_by_match_team(
        self,
        match_team_id: int,
        match_status: int | None = None,
        new_lineup: str | None = None,
    ) -> bool:
        """
        Load lineup data by match team ID.

        Args:
            match_team_id: ID of the match team
            match_status: Optional match status override
            new_lineup: Optional new lineup string

        Returns:
            True if loaded successfully, False otherwise
        """
        return self.load(
            self.read_by_match_team(match_team_id), match_status, new_lineup
        )

    def load_by_team_id(
        self,
        team_id: int,
        competition_type: int,
        competition_match_day: int,
        match_status: int | None = None,
        new_lineup: str | None = None,
    ) -> bool:
        """
        Load lineup data by team ID, competition type, and match day.

        Args:
            team_id: ID of the team
            competition_type: Type of competition
            competition_match_day: Match day in the competition
            match_status: Optional match status override
            new_lineup: Optional new lineup string

        Returns:
            True if loaded successfully, False otherwise
        """
        return self.load(
            self.read_by_team_id(team_id, competition_type, competition_match_day),
            match_status,
            new_lineup,
        )

    def load(
        self,
        match_team: RowMapping | None,
        match_status: int | None = None,
        new_lineup: str | None = None,
    ) -> bool:
        """
        Load lineup data from a match team record.

        Args:
            match_team: Database row mapping for the match team
            match_status: Optional match status override
            new_lineup: Optional new lineup string

        Returns:
            True if loaded successfully, False otherwise

        This method orchestrates the loading process:
        1. Set base values from the match team
        2. Load team members
        3. Process the lineup data
        4. Handle formation validation and substitution calculations
        """
        if not self._set_values(match_team, match_status):
            return self._set_values()
        if not self._set_team_members(match_team):
            return self._set_values()
        if not self._process_lineup(match_team, new_lineup):
            return self._set_values()

        # For non-finished matches, validate and calculate formation
        if self.match_status != MatchStatusConstants.FINISHED:
            self._substitutes = []
            self._check_team_members()
            dp_count = self._calc_formation()
            if self.match_status == MatchStatusConstants.PLAYING:
                self._calc_substitutes(dp_count)
        return True

    def save_lineup(self, force: bool = False) -> bool:
        """_summary_

        Args:
            force (bool, optional): _description_. Defaults to False.

        Returns:
            bool: _description_
        """
        if self._match_team_id is None:
            return False
        lineup = self.pack()
        if not force and lineup == self._lineup_txt:
            return False
        self._db.execute(
            text(
                "UPDATE `MatchTeams` SET `lineup` = :lineup WHERE `matchTeamID` = :matchTeamID"
            ),
            {"lineup": lineup, "matchTeamID": self._match_team_id},
        )
        self._lineup_txt = lineup
        return True

    def save_match_status(
        self, match_status: int | None = None, force: bool = False
    ) -> bool:
        """_summary_

        Args:
            match_status (int | None, optional): _description_. Defaults to None.
            force (bool, optional): _description_. Defaults to False.

        Returns:
            bool: _description_
        """
        if self._match_id is None:
            return False
        match_status = MatchStatusConstants.verify(
            match_status if match_status is not None else self.match_status
        )
        if match_status is None:
            return False
        if not force and match_status == self._db_match_status:
            return False
        self._db.execute(
            text(
                "UPDATE `Matches` SET `matchStatus` = :matchStatus WHERE `matchID` = :matchID"
            ),
            {"matchStatus": match_status, "matchID": self._match_id},
        )
        self._db_match_status = match_status
        return True

    def get_key_data(self, key: str) -> dict[str, Any]:
        """
        Get data for a specific key with normalized draft position.

        Args:
            key: The key to look up

        Returns:
            Dictionary containing key data with normalized draft position
        """
        data = self._get_key_data(key)
        if not isinstance(data, dict):
            data = {}
        data["draftPosition"] = DraftPositionConstants.normalize(
            data.get("draftPosition")
        )
        return data

    @property
    def substitutes(self) -> list[str]:
        """
        Get the list of players that were substituted.

        Returns:
            List of player keys that have been substituted
        """
        return self._substitutes

    def unpack(self, data: str | PackedData | None = None) -> bool:
        """
        Unpack lineup data from a string or PackedData object.

        Args:
            data: The data to unpack (string, PackedData, or None)

        Returns:
            True if unpacked successfully, False otherwise

        This method handles the FLAG marker for substitutes and extracts
        the substitution information.
        """
        self._substitutes = []
        if isinstance(data, str):
            # Handle the self.FLAG by temporarily removing it
            old_data = data
            data = data.replace(self.FLAG + MKeys.SUFFIX, MKeys.SUFFIX)

        if super().unpack(data, 3):
            if isinstance(data, str):
                # Add the flagged keys to substitutes
                for i in (0, 1):
                    for key in self._groups[i]:
                        if key.startswith(MKeys.PLAYER) and key + self.FLAG in old_data:
                            self._substitutes.append(key)
            elif isinstance(data, Lineup):
                # Copy substitutes from the source lineup
                self._substitutes = data.substitutes
            return True
        return False

    def pack(self) -> str:
        """
        Pack the lineup data into a string with substitute flags.

        Returns:
            String representation of the lineup with flags for substitutes
        """
        txt = super().pack()
        for s in self.substitutes:
            # Add the flag to the keys in self._substitutes
            txt = txt.replace(s + MKeys.SUFFIX, s + self.FLAG + MKeys.SUFFIX)
        return txt

    def get_members(self) -> Iterator[dict[str, Any]]:
        for g, keys in enumerate(self._groups):
            for key in keys:
                data = dict(self.get_key_data(key))
                data["realTeamMemberKey"] = key
                data["matchTeamID"] = self.match_team_id
                data["teamID"] = self.team_id
                data["matchStatus"] = self.match_status
                data["matchTeamMemberRole"] = g + 1
                if key in self._substitutes:
                    data["matchTeamMemberPlayed"] = 1 if g == 1 else 0
                else:
                    data["matchTeamMemberPlayed"] = 1 if g == 0 else 0

                yield data

    def _set_values(
        self,
        match_team: RowMapping | None = None,
        match_status: int | None = None,
    ) -> bool:
        """
        Set base values from the match team data.

        Args:
            match_team: Database row mapping for the match team
            match_status: Optional match status override

        Returns:
            True if match_team is not None, False otherwise
        """
        self._team_members = []
        self._substitutes: list[str] = []
        self._lineup_txt = MKeys.DELIM * 2
        self._match_team_id = match_team["matchTeamID"] if match_team else None
        self._match_id = match_team["matchID"] if match_team else None
        self._team_id = match_team["teamID"] if match_team else None
        self._user_id = match_team["userID"] if match_team else None
        self._db_lineup = match_team["lineup"] if match_team else None
        self._match_team_num = match_team["matchTeamNum"] if match_team else None
        self._real_competition_id = (
            match_team["realCompetitionID"] if match_team else None
        )
        self._real_competition_match_day = (
            match_team["realCompetitionMatchDay"] if match_team else None
        )
        self._competition_type = CompetitionTypeConstants.verify(
            match_team["competitionType"] if match_team else None
        )
        self._competition_match_day = (
            match_team["competitionMatchDay"] if match_team else None
        )
        self._match_day_map_key = match_team["matchDayMapKey"] if match_team else None
        self._db_match_status = MatchStatusConstants.verify(
            match_team["matchStatus"] if match_team else None
        )
        self._chosen_match_status = MatchStatusConstants.verify(match_status)
        return match_team is not None

    def _set_team_members(self, match_team: RowMapping | None = None) -> bool:
        """
        Set team members based on match status.

        Args:
            match_team: Database row mapping for the match team

        Returns:
            True if team members were set successfully, False otherwise

        Team members are only loaded for matches that haven't finished,
        as finished matches don't need active roster data.
        """
        if self.match_status in (
            MatchStatusConstants.NOT_STARTED,
            MatchStatusConstants.PLAYING,
        ):
            self._team_members = MKeys.to_list(match_team["teamMembers"] or "", True)
            if not isinstance(self._team_members, list) or len(self._team_members) <= 0:
                self._team_members = []
                return self._set_values()
        elif self.match_status != MatchStatusConstants.FINISHED:
            return self._set_values()
        return True

    def _process_lineup(
        self, match_team: RowMapping | None = None, new_lineup: str | None = None
    ) -> bool:
        """
        Process and clean the lineup data.

        Args:
            match_team: Database row mapping for the match team
            new_lineup: Optional new lineup string

        Returns:
            True if lineup was processed successfully, False otherwise

        This method handles:
        1. Using a new lineup if provided (only for NOT_STARTED matches)
        2. Falling back to previous lineup if current is empty
        3. Cleaning up the lineup data
        4. Unpacking the cleaned data
        """
        if new_lineup is not None:
            # A request to change the lineup
            if self.match_status == MatchStatusConstants.NOT_STARTED:
                lineup_txt = new_lineup
            else:
                return self._set_values()
        elif (
            Lineup.is_empty(match_team["lineup"])
            and self.match_status != MatchStatusConstants.FINISHED
        ):
            # Handle empty lineup
            lineup_txt = self._get_prev_lineup()
        else:
            # Get the current lineup
            lineup_txt = match_team["lineup"] or ""

        lineup_txt = self.clean_up(lineup_txt)
        if lineup_txt is None:
            return self._set_values()

        if not self.unpack(lineup_txt):
            return self._set_values()
        self._lineup_txt = lineup_txt
        return True

    def _get_prev_lineup(self) -> str:
        """
        Retrieve the previous lineup for the same team in the competition.

        Returns:
            The previous lineup string or empty lineup if none found
        """
        sql = """
              SELECT `lineup`
                 FROM `MatchTeams` `mt`
                 INNER JOIN `Matches` `m` ON `m`.`matchID` = `mt`.`matchID`
                 WHERE `mt`.`teamID` = :teamID
                   AND `m`.`competitionType` = :competitionType
                   AND `m`.`competitionMatchDay` < :competitionMatchDay
                 ORDER BY `m`.`competitionMatchDay` DESC
              """
        rows = (
            self._db.execute(
                text(sql),
                {
                    "teamID": self._team_id,
                    "competitionType": self._competition_type,
                    "competitionMatchDay": self._competition_match_day,
                },
            )
            .mappings()
            .all()
        )

        # Find the first non-empty lineup from previous match days
        for row in rows:
            if not Lineup.is_empty(row["lineup"]):
                lineup_txt = self.clean_up(row["lineup"])
                if lineup_txt is not None:
                    return lineup_txt

        # Return empty lineup if no previous lineup found
        return MKeys.DELIM * 2

    def _calc_formation(self) -> dict[str, int]:
        """
        Calculate and validate the formation from the current lineup.

        Returns:
            Dictionary of position counts for the current formation

        For PLAYING matches, this also finalizes the formation by
        moving additional players to their correct groups.
        """
        dp_count, formation = self._check_formation()
        if self.match_status == MatchStatusConstants.PLAYING:
            dp_count = self._finish_formation(dp_count, formation)
        return dp_count

    def _check_formation(self) -> tuple[dict[str, int], str | None]:
        """
        Check if the lineup forms a valid formation.

        Returns:
            tuple containing:
                - dict[str, int]: Position counts
                - str | None: Formation name if valid, None otherwise

        This method processes group 0 players first and moves invalid
        players to other groups.
        """
        formation: str | None = None
        group_0: GroupData = []
        dp_count: dict[str, int] = {}

        # Process players in group 0
        for k in self._groups[0]:
            dp = self.get_key_data(k).get("draftPosition")
            if dp is None:
                continue
            elif formation is None:
                valid, form, dp_count = Formations.formation_found(dp_count, dp)
                if valid:
                    group_0.append(k)
                    if isinstance(form, str):
                        formation = form
                    continue
            # Move invalid players to appropriate groups
            g = 1 if k.startswith(MKeys.PLAYER) else 2
            self._groups[g].append(k)

        self._groups[0] = group_0
        return dp_count, formation

    def _finish_formation(
        self, dp_count: dict[str, int], formation: str | None
    ) -> dict[str, int]:
        """
        Finalize formation by processing remaining groups.

        Args:
            dp_count: Current position counts
            formation: Current formation name

        Returns:
            Updated position counts

        This method processes groups 1 and 2, moving valid players
        to group 0 when they fit the formation.
        """
        for g in (1, 2):
            group = []
            for k in self._groups[g]:
                dp = self.get_key_data(k).get("draftPosition")
                if dp is None:
                    continue
                elif formation is None:
                    valid, form, dp_count = Formations.formation_found(dp_count, dp)
                    if valid:
                        self._groups[0].append(k)
                        if isinstance(form, str):
                            formation = form
                        continue
                group.append(k)
            self._groups[g] = group
        return dp_count

    def _calc_substitutes(self, dp_count: dict[str, int]) -> None:
        """
        Calculate and apply substitutions for the match.

        Args:
            dp_count: Current position counts before substitutions

        This method determines which players should be substituted based on:
        1. Players ready to exit (finished their match)
        2. Available substitutes
        3. Formation validity
        4. Maximum substitution limits
        """
        self._substitutes = []
        ready_to_exit = self._get_ready_to_exit()
        ready_to_enter: dict[str, str] = {}

        while True:
            k_out, k_in, ready_to_enter = self._next_substitute(
                dp_count, ready_to_exit, ready_to_enter
            )
            if not isinstance(k_out, str) or not isinstance(k_in, str):
                # No more substitutes available
                break

            # Apply the substitution
            self._substitutes.append(k_in)
            self._substitutes.append(k_out)
            del ready_to_exit[k_out]

            # Check termination conditions
            if len(ready_to_exit) <= 0:
                # No more players ready to exit
                break
            if len(self._substitutes) > 2 * LineupConstants.MAX_SUBSTITUTES:
                # Reached maximum substitutions
                break

    def _get_ready_to_exit(self) -> dict[str, str]:
        """
        Get players ready to be substituted out.

        Returns:
            Dictionary mapping player keys to their draft positions
            for players who have finished their match and are eligible for substitution
        """
        ready_to_exit: dict[str, str] = {}
        for k in self._groups[0]:
            if k.startswith(MKeys.PLAYER):
                data = self.get_key_data(k)
                if data.get("realMatchStatus") == RealMatchStatus.FINISHED and data.get(
                    "matchDayPlayed"
                ):
                    ready_to_exit[k] = data.get("draftPosition")
        return ready_to_exit

    def _next_substitute(
        self,
        dp_count: dict[str, int],
        ready_to_exit: dict[str, str],
        ready_to_enter: dict[str, str],
    ) -> tuple[str | None, str | None, dict[str, str]]:
        """
        Find the next valid substitution.

        Args:
            dp_count: Current position counts
            ready_to_exit: Players ready to exit with their positions
            ready_to_enter: Players ready to enter with their positions

        Returns:
            tuple containing:
                - str | None: Key of player to exit
                - str | None: Key of player to enter
                - dict[str, str]: Updated ready_to_enter dictionary

        This method tries to find a valid substitution that maintains
        formation validity.
        """
        for k_in in self._groups[1]:
            if k_in in self._substitutes:
                # Player already substituted
                continue
            if k_in not in ready_to_enter:
                # Cache the draft position
                ready_to_enter[k_in] = self.get_key_data(k_in).get("draftPosition")

            dp_in = ready_to_enter[k_in]
            if dp_in is None or dp_in not in dp_count:
                continue

            for k_out, dp_out in ready_to_exit.items():
                if k_out in self._substitutes:
                    continue
                if dp_out is None or dp_out not in dp_count:
                    continue

                # Try removing k_out
                dp_count[dp_out] -= 1
                # Check if adding k_in results in a valid formation
                valid, _, dp_count = Formations.formation_found(dp_count, dp_in)
                if valid:
                    # Found a valid substitution
                    return k_out, k_in, ready_to_enter
                else:
                    # Revert the removal
                    dp_count[dp_out] += 1

        # No valid substitution found
        return None, None, ready_to_enter

    def _check_team_members(self) -> None:
        """
        Clean up team members by removing invalid keys and adding missing ones.

        This method ensures that:
        1. Only keys present in team_members are kept
        2. All team_members are included in the appropriate groups
        3. Players go to group 1, teams go to group 2
        """
        # Remove keys not in team_members
        tm = set(self._team_members)
        for i in range(self.size):
            self._groups[i] = [x for x in self._groups[i] if x in tm]

        # Add missing team_members
        keys = {k for _, k in self.keys()}
        for k in self._team_members:
            if k not in keys:
                # Players go to group 1, Teams to group 2
                g = 1 if k.startswith(MKeys.PLAYER) else 2
                self._groups[g].append(k)
