from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.orm import Session

from app.constants import DraftPositionConstants, RealMatchStatus
from app.services import QueryService
from app.utils.rtm_keys import Keys


class Reader(ABC):
    def __init__(self, db: Session):
        super().__init__()
        self._db = db
        self._cache: dict = {}

    @abstractmethod
    def get_row(self, *args, **kargs) -> dict:
        pass

    def get(self, *args, default: Any = None, **kargs) -> Any:
        *row_args, field = args
        return self.get_row(*row_args, **kargs).get(field, default)

    @abstractmethod
    def load(self, *args, **kargs):
        pass

    def reset(self) -> None:
        self._cache = {}


class KeysReader(Reader):
    def get_row(self, key: str) -> dict:
        if key not in self._cache:
            self.load(key)
            if key not in self._cache:
                self._cache[key] = {}
        return self._cache[key]

    def get_dp(self, key: str) -> str | None:
        dp =  self.get(key, "draftPosition")
        return dp if dp in DraftPositionConstants.valid_values() else None

    def real_match_finished(self, key: str) -> bool:
        return bool(self.get(key, "realMatchStatus") == RealMatchStatus.FINISHED)

    def real_played(self, key: str) -> bool:
        if not self.real_match_finished(key):
            return False
        return bool(self.get(key, "matchDayPlayed")) if Keys.is_player(key) else True

    def _clean(
        self, key: str | None = None, keys: list[str] | None = None
    ) -> list[str]:
        merged = list(keys) if keys else []
        if key is not None:
            merged.append(key)
        return [k for k in merged if Keys.isvalid(k) and k not in self._cache]

    def _check_dp(self, data: dict) -> dict:
        data["draftPosition"] = DraftPositionConstants.normalize(
            data.get("draftPosition")
        )
        return data


class RTMReader(KeysReader):
    def __init__(self, db: Session):
        super().__init__(db)

    def load(self, key: str | None = None, keys: list[str] | None = None):
        for data in QueryService.get_real_team_members_by_keys(
            self._db, self._clean(key, keys)
        ).values():
            self._cache[data["realTeamMemberKey"]] = self._check_dp(data)


class RSReader(KeysReader):
    def __init__(
        self, db: Session, real_competition_id: int, real_competition_match_day: int
    ):
        super().__init__(db)
        self._rc_id = real_competition_id
        self._rc_md = real_competition_match_day

    def get_score(self, key) -> int | None:
        return self.get(key, "matchPointsL1", default=0)

    def load(self, key: str | None = None, keys: list[str] | None = None):
        for data in QueryService.get_real_standings_by_keys(
            self._db, rc_id=self._rc_id, rc_md=self._rc_md, keys=self._clean(key, keys)
        ):
            self._cache[data["realTeamMemberKey"]] = self._check_dp(data)
