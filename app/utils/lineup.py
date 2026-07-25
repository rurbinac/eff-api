import re

from app.constants import DraftPositionConstants
from app.utils.member_keys import MKeys, PackedData

FORMATIONS_TXT = "442,433,451"
_validFormations = {}

for vf in FORMATIONS_TXT.replace(" ", "").split(","):
    if re.match(r"^[1-9][1-9][1-9]$", vf) and vf not in _validFormations:
        _validFormations[vf] = {
            DraftPositionConstants.GOALKEEPER: 1,
            DraftPositionConstants.DEFENDER: int(vf[0]),
            DraftPositionConstants.MIDFIELDER: int(vf[1]),
            DraftPositionConstants.STRIKER: int(vf[2]),
            DraftPositionConstants.EPL_TEAM: 1,
        }


class LineUp(MKeys):

    FLAG = "!"

    @staticmethod
    def to_str(keys, one_level = False):
        value = super().to_str(keys, one_level)
        return value

    @staticmethod
    def from_ids(
        team_ids: int | list[int] | None,
        player_ids: int | list[int] | None,
        sub_player_ids: int | list[int] | None,
    ) -> str | None:
        t_ids = MKeys.from_team_ids(team_ids)
        p_ids = MKeys.from_player_ids(player_ids)
        s_ids = MKeys.from_player_ids(sub_player_ids)
        if t_ids is not None and p_ids is not None and s_ids is not None:
            if t_ids:
                t_0, t_1 = t_ids.split(MKeys.SUFFIX, 1)
                t_0 = t_0 + MKeys.SUFFIX
            else:
                t_0, t_1 = "", ""
            return p_ids + t_0 + MKeys.DELIM + s_ids + MKeys.DELIM + t_1
        return None

    @staticmethod
    def is_empty(value: str | list | MKeys | None) -> bool:
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
        Cleans and reorganizes a lineup text string by categorizing items into teams.

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
        if LineUp.is_empty(lineup_txt):
            return MKeys.DELIM * 2
        if lineup_txt.count(MKeys.DELIM) != 2:
            return None
        first_team = True
        txt: list[str] = ["", "", ""]
        for i, t in enumerate(lineup_txt.split(MKeys.DELIM)):
            if t == "":
                continue
            if not t.endswith(MKeys.SUFFIX):
                return None
            for k in t[:-1].split(MKeys.SUFFIX):
                prefix, _ = MKeys.split_key(k)
                match prefix:
                    case MKeys.PLAYER:
                        # Players will go to 0 or 1
                        n = 0 if i == 0 else 1
                    case MKeys.TEAM:
                        # The first team can be in 0, the others in 2
                        n = 0 if i == 0 and first_team else 2
                        first_team = False
                    case _:
                        return None
                # Add the processed item to the appropriate bucket (with SUFFIX)
                txt[n] += k + MKeys.SUFFIX
        # Return the reorganized string with three DELIM-separated groups
        return MKeys.DELIM.join(txt)

    def __init__(self):
        super().__init__(False)
        self._substitutes: PackedData = self._empty_subs()

    def init_ToShowPreMatch(self, lineup_txt: str, team_members: str) -> bool:
        tm = MKeys.to_list(team_members.replace(LineUp.FLAG, ""))
        if isinstance(tm, list) and len(tm) == 1 and len(tm[0]) > 0:
            if not self.unpack(self.clean_up(lineup_txt)):
                return False

        # if ($this->toRTMKeys($teamMembers, $members) &&
        #     $this->unpack($this->cleanBench($lineupTxt))) {
        #     $this->resetSubstitutes();
        #     $this->checkGroups($members);
        #     $this->cleanFormation();
        #     return true;
        # }
        # $this->reset();
        # return false;

    def _empty_subs(self) -> list[list[str]]:
        return [[], [], []]
