from datetime import datetime

from sqlalchemy.orm import Session

from app.constants import MatchCreationConstants
from app.actions.draft.match_factory import DivisionRRFactory, DivisionKOFactory, LeagueKOFactory
from app.services import QueryService


class DraftClose:
    def __init__(self, db: Session, leagueID: int, user_id: int, now: datetime):
        self._db = db
        self._user_id = user_id
        self._now = now
        self._divisions = self._load_divisions(leagueID)

    def execute(self) -> None:
        for i in range(len(self._divisions)):
            divRR = DivisionRRFactory(self._db, self._divisions[i], self._user_id, self._now)
            if divRR.build():
                self._divisions[i]["divisionMatches"] = MatchCreationConstants.CREATING
            divKO = DivisionKOFactory(self._db, self._divisions[i], self._user_id, self._now)
            if divKO.build():
                self._divisions[i]["divisionMatches"] = MatchCreationConstants.CREATED
        leaKO = LeagueKOFactory(self._db, self._divisions, self._user_id, self._now)
        if leaKO.build():
            self._divisions = leaKO.divisions

    def _load_divisions(self, leagueID: int) -> list[dict]:
        return QueryService.get_divisions_by_league(self._db, leagueID)
