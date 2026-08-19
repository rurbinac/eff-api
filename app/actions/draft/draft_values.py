import json
from collections.abc import Iterator
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.constants import DraftPositionConstants
from app.exceptions import CannotSaveException
from app.models import Division, Team
from app.utils import optimistic_update
from app.utils.member_keys import MKeys

EPL_TEAM = DraftPositionConstants.EPL_TEAM


class DraftValues:
    """Repository for the draft process state."""

    def __init__(self, db: Session, division_id: int):
        self._db = db
        self._division_id = division_id
        self._league: dict | None = None
        self._division: dict | None = None
        self._teams: list[dict] | None = None
        self._members: dict[str, list] | None = None
        self._old_division: dict = {}
        self._old_team: dict = {}
        self._curr_team_num: int | None = None

    @property
    def division(self) -> dict | None:
        return self._division

    @property
    def old_division(self) -> dict:
        return self._old_division

    @property
    def curr_team_num(self) -> int | None:
        return self._curr_team_num

    @property
    def team(self) -> dict | None:
        if not isinstance(self._teams, list) or self._curr_team_num is None:
            return None
        if self._curr_team_num < 0 or self._curr_team_num >= len(self._teams):
            return None
        return self._teams[self._curr_team_num]

    @property
    def old_team(self) -> dict:
        return self._old_team

    @property
    def teams(self) -> list[dict]:
        return self._teams or []

    def init_curr_team_num(self) -> None:
        if self._division and self._division.get("draftingTeamOrder") is not None:
            self._curr_team_num = self._division["draftingTeamOrder"] - 1
        else:
            self._curr_team_num = None

    def load_division(self, force: bool = False) -> bool:
        if force or self._division is None:
            self._division = None
            division = self._db.get(Division, self._division_id)
            self._division = division.model_dump() if division else None
        self.init_curr_team_num()
        return self._division is not None

    def load_teams(self, force: bool = False) -> bool:
        if not force and self._teams is not None:
            return True
        self._teams = None
        if self._division is None:
            self._teams = None
            return False
        stmt = (
            select(Team)
            .where(Team.divisionID == self._division_id)
            .order_by(Team.draftOrder)
        )
        self._teams = [t.model_dump() for t in self._db.execute(stmt).scalars().all()]
        if len(self._teams) > 0:
            return True
        self._teams = None
        return False

    def load_members(self, force: bool = False) -> bool:
        if not force and self._members is not None:
            return True
        self._members = None
        if not isinstance(self._teams, list) or self._division is None:
            return False
        stmt = text("""
            SELECT realTeamMemberKey, draftPosition
            FROM RealTeamMembers
            WHERE baseRealCompetitionID = :baseRealCompetitionID
            ORDER BY ranking
        """)
        rows = self._db.execute(
            stmt, {"baseRealCompetitionID": self._division["baseRealCompetitionID"]}
        ).mappings()
        self._members = {
            row["realTeamMemberKey"]: [row["draftPosition"], None] for row in rows
        }
        # Associate team IDs with members based on the teams' teamMembers field
        if len(self._members) > 0:
            for team in self._teams:
                team_id = team.get("teamID")
                if team_id is not None and team.get("teamMembers", "") != "":
                    for key in team["teamMembers"].split(MKeys.SUFFIX):
                        if key in self._members:
                            self._members[key][1] = team_id
            return True
        self._members = None
        return False

    def get_member_keys(self) -> Iterator[str]:
        if isinstance(self._members, dict):
            for key in self._members.keys():
                yield key

    def get_dp(self, key: str) -> str | None:
        if self._members is None:
            return None
        return self._members.get(key, [None, None])[0]

    def get_member_team_id(self, key: str) -> int | None:
        if self._members is None:
            return None
        return self._members.get(key, [None, None])[1]

    def set_member_team_id(
        self, key: str, team_id: int, freeze_values: bool = False
    ) -> bool:
        if self._members is None or key not in self._members:
            return False
        dp = self._members.get(key, [None, None])[0]
        if dp is None:
            return False
        self._members[key][1] = team_id
        if self._teams is not None:
            for team in self._teams:
                if team.get("teamID") == team_id:
                    if freeze_values:
                        self.freeze_team_values(
                            "teamMembers", "draftMembers", f"cnt{dp}"
                        )
                    teamMembers = team.get("teamMembers", "") + key + MKeys.SUFFIX
                    team["teamMembers"] = teamMembers
                    team["draftMembers"] = teamMembers
                    team[f"cnt{dp}"] += 1
                    if dp != EPL_TEAM:
                        if freeze_values:
                            self.freeze_team_values("cntPlayer")
                        team["cntPlayer"] += 1
                    break
        return True

    def set_division_values(
        self, values: dict[str, Any], save_old: bool = False
    ) -> None:
        if isinstance(self._division, dict):
            if save_old:
                self.freeze_division_values(*values.keys())
            for name, value in values.items():
                self._division[name] = value

    def freeze_division_values(self, *names: str) -> None:
        if isinstance(self._division, dict):
            for name in names:
                if name in self._division and name not in self._old_division:
                    self._old_division[name] = self._division[name]

    def set_team_values(self, values: dict[str, Any], save_old: bool = False) -> None:
        if isinstance(self.team, dict):
            if save_old:
                self.freeze_team_values(*values.keys())
            for name, value in values.items():
                self._teams[self._curr_team_num][name] = value

    def freeze_team_values(self, *names: str) -> None:
        team = self.team
        if isinstance(team, dict):
            for name in names:
                if name in team and name not in self._old_team:
                    self._old_team[name] = team[name]

    def save_division(self, include_curr_team: bool = False) -> bool:
        if not self._old_division or self._division is None:
            return False

        success = optimistic_update(
            self._db,
            model=Division,
            pk={"divisionID": self._division["divisionID"]},
            new_values={k: self._division[k] for k in self._old_division},
            old_values=self._old_division,
        )
        if not success:
            raise CannotSaveException("Division", "was updated by another request")

        if include_curr_team:
            team = self.team
            if team and self._old_team:
                team_success = optimistic_update(
                    self._db,
                    model=Team,
                    pk={"teamID": team["teamID"]},
                    new_values={k: team[k] for k in self._old_team},
                    old_values=self._old_team,
                )
                if not team_success:
                    raise CannotSaveException("Team", "was updated by another request")

        self._db.commit()
        self._old_division = {}
        self._old_team = {}
        return True

    def get_drafting_users(self, only_signed: bool = True) -> list[int]:
        users: list[int] = []
        if self._division is None or "draftingUsers" not in self._division:
            return users

        raw = self._division["draftingUsers"]
        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
            if isinstance(data, dict):
                for user_id_str, entry in data.items():
                    is_signed = (
                        isinstance(entry, list) and len(entry) > 0 and entry[0] == 1
                    )
                    if only_signed and not is_signed:
                        continue
                    try:
                        user_id = int(user_id_str)
                        if user_id not in users:
                            users.append(user_id)
                    except (ValueError, TypeError):
                        pass
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass

        return users
