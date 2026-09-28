from __future__ import annotations

import re
from collections.abc import Generator, Iterator
from typing import Any, ClassVar, Final

from app.constants import (
    DraftPositionConstants,
    LineupConstants,
)
from app.utils.readers import RSReader
from app.utils.rtm_keys import KeyGroups, Keys


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


class Lineup(KeyGroups):
    """
    Manages football lineup data including players, teams, and substitutions.

    Inherits from KeyGroups (3 fixed slots):
      slot 0 — starters + first EPL team
      slot 1 — substitute bench players
      slot 2 — additional EPL teams
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
        t_ids = Keys.to_str(
            Keys.build_team_keys(team_ids) if team_ids is not None else None
        )
        p_ids = Keys.to_str(
            Keys.build_player_keys(player_ids) if player_ids is not None else None
        )
        s_ids = Keys.to_str(
            Keys.build_player_keys(sub_player_ids)
            if sub_player_ids is not None
            else None
        )
        if t_ids is not None and p_ids is not None and s_ids is not None:
            if t_ids:
                # Split teams into first (group 0) and second (group 2)
                t_0, t_1 = t_ids.split(Keys.SUFFIX, 1)
                t_0 += Keys.SUFFIX
            else:
                t_0, t_1 = "", ""
            # Format: players + first team | substitutes | second team
            return p_ids + t_0 + KeyGroups.DELIM + s_ids + KeyGroups.DELIM + t_1
        return None

    @staticmethod
    def is_empty(value: str | list | KeyGroups | None) -> bool:
        """
        Check if a lineup value is empty or contains no meaningful data.

        Args:
            value: The value to check (string, list, KeyGroups, or None)

        Returns:
            True if empty, False otherwise
        """
        if value is None:
            return True
        elif isinstance(value, KeyGroups):
            return value.count() == 0 and len(value) == 3
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
            return value == "" or value == KeyGroups.DELIM * 2
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
            return KeyGroups.DELIM * 2
        # Validate delimiter count (should be exactly 3 groups)
        if lineup_txt.count(KeyGroups.DELIM) != 2:
            return None

        first_team = True
        txt: list[str] = ["", "", ""]

        for i, t in enumerate(lineup_txt.split(KeyGroups.DELIM)):
            if t == "":
                continue
            # Each item must end with SUFFIX
            if not t.endswith(Keys.SUFFIX):
                return None

            for k in t[:-1].split(Keys.SUFFIX):
                prefix, _ = Keys.split(k)
                match prefix:
                    case Keys.PLAYER:
                        # Players go to group 0 or 1 based on source group
                        n = 0 if i == 0 else 1
                    case Keys.TEAM:
                        # First team goes to group 0, subsequent teams to group 2
                        n = 0 if i == 0 and first_team else 2
                        first_team = False
                    case _:
                        return None
                # Add the processed item to the appropriate bucket (with SUFFIX)
                txt[n] += k + Keys.SUFFIX

        # Return the reorganized string with three DELIM-separated groups
        return KeyGroups.DELIM.join(txt)

    def __init__(
        self,
        reader: RSReader,
        match_started: bool = True,
    ):
        super().__init__(3, allow_dups=False)
        self._reader = reader
        self._match_started = match_started
        self._substitutes: list[str] = []
        self._team_members: list[str] | None = None

    @property
    def before_match(self) -> bool:
        return self._match_started and isinstance(self._team_members, list)

    @property
    def in_match(self) -> bool:
        return not self._match_started and isinstance(self._team_members, list)

    @property
    def after_match(self) -> bool:
        return not isinstance(self._team_members, list)


    @property
    def substitutes(self) -> list[str]:
        """
        Get the list of players that were substituted.

        Returns:
            List of player keys that have been substituted
        """
        return self._substitutes

    def is_equal(self, lineup: str | Lineup) -> bool:
        return self.pack() == (lineup.pack() if isinstance(lineup, Lineup) else lineup)

    def unpack(
        self,
        data: str | KeyGroups | Lineup | None = None,
        team_members: str | list[str] | Keys | None = None,
    ) -> bool:
        self._substitutes = []
        self._team_members = None
        if isinstance(data, str):
            old_data = data
            data = data.replace(self.FLAG + Keys.SUFFIX, Keys.SUFFIX)
            if not super().unpack(data):
                return False
            for i in (0, 1):
                for key in self._keys[i]:
                    if key.startswith(Keys.PLAYER) and key + self.FLAG in old_data:
                        self._substitutes.append(key)
        elif isinstance(data, Lineup):
            if not super().unpack(data):
                return False
            self._substitutes = list(data.substitutes)
        elif isinstance(data, KeyGroups):
            if len(data) != 3 or not super().unpack(data):
                return False
        elif data is None:
            self.reset()
        else:
            return False
        if not self.after_match:
            parsed = Keys.to_list(team_members)
            if parsed is None:
                return False
            self._team_members = parsed
            self._check_team_members()
            dp_count = self._calc_formation()
            if self.in_match:
                self._calc_substitutes(dp_count)
        return True

    def pack(self) -> str:
        txt = super().pack()
        for s in self.substitutes:
            txt = txt.replace(s + Keys.SUFFIX, s + self.FLAG + Keys.SUFFIX)
        return txt

    def score(self) -> int:
        return sum(self._reader.get_score(k) for k in self.get_playing_keys())

    def get_playing_keys(self) -> Generator[str, None, None]:
        yield from (k for k in self._keys[0].data if k not in self._substitutes)
        yield from (k for k in self._keys[1].data if k in self._substitutes)

    def get_members(self, **kwargs) -> Iterator[dict[str, Any]]:
        for g, slot in enumerate(self._keys):
            for key in slot:
                data = dict(self._reader.get_row(key))
                data["realTeamMemberKey"] = key
                data.update(kwargs)
                data["matchTeamMemberRole"] = g + 1
                if key in self._substitutes:
                    data["matchTeamMemberPlayed"] = 1 if g == 1 else 0
                else:
                    data["matchTeamMemberPlayed"] = 1 if g == 0 else 0

                yield data

    def _calc_formation(self) -> dict[str, int]:
        """
        Calculate and validate the formation from the current lineup.

        Returns:
            Dictionary of position counts for the current formation

        For PLAYING matches, this also finalizes the formation by
        moving additional players to their correct groups.
        """
        dp_count, formation = self._check_formation()
        if self.before_match:
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
        group_0: list[str] = []
        dp_count: dict[str, int] = {}

        for k in self._keys[0]:
            dp = self._reader.get_dp(k)
            if dp is None:
                continue
            elif formation is None:
                valid, form, dp_count = Formations.formation_found(dp_count, dp)
                if valid:
                    group_0.append(k)
                    if isinstance(form, str):
                        formation = form
                    continue
            # Move overflow to subs (1) or teams (2); bypass dup-check since key is still in slot 0
            g = 1 if k.startswith(Keys.PLAYER) else 2
            self._keys[g].data.append(k)

        self._keys[0].data = group_0
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
            remaining = []
            for k in self._keys[g]:
                dp = self._reader.get_dp(k)
                if dp is None:
                    continue
                elif formation is None:
                    valid, form, dp_count = Formations.formation_found(dp_count, dp)
                    if valid:
                        self._keys[0].data.append(k)
                        if isinstance(form, str):
                            formation = form
                        continue
                remaining.append(k)
            self._keys[g].data = remaining
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
        for k in self._keys[0]:
            if Keys.is_player(k) and self._reader.real_played(k):
                ready_to_exit[k] = self._reader.get_dp(k)
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
        for k_in in self._keys[1]:
            if k_in in self._substitutes:
                # Player already substituted
                continue
            if k_in not in ready_to_enter:
                # Cache the draft position
                ready_to_enter[k_in] = self._reader.get_dp(k_in)

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
        tm = set(self._team_members)
        for slot in self._keys:
            slot.data = [x for x in slot if x in tm]

        keys = {key for slot in self._keys for key in slot}
        for k in self._team_members:
            if k not in keys:
                g = 1 if k.startswith(Keys.PLAYER) else 2
                self._keys[g].data.append(k)
