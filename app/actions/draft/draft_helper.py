from sqlalchemy.orm import Session

from app.actions.draft.draft_base import DraftPause, DraftRestart, DraftStart
from app.actions.draft.draft_close import DraftClose
from app.actions.draft.draft_member import DraftMember
from app.actions.draft.draft_notice import DraftNotice
from app.actions.draft.draft_values import DraftValues
from app.constants import DraftConstants
from app.context import RequestContext

class DraftHelper:
    def __init__(self, db: Session, user_id: int, division_id: int) -> None:
        self._db: Session = db
        self._user_id: int = user_id
        self._draft_values: DraftValues = DraftValues(db, division_id)
        self._draft_notice: DraftNotice = DraftNotice(division_id)
        if not self._draft_values.load_division():
            raise ValueError(f"Division {division_id} not found")
        if not self._draft_values.load_teams():
            raise ValueError(f"Teams for division {division_id} not found")

    @property
    def db(self) -> Session:
        return self._db

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def draft_values(self) -> DraftValues:
        return self._draft_values

    @property
    def draft_notice(self) -> DraftNotice:
        return self._draft_notice

    def start(self) -> dict:
        DraftStart(self).execute()
        return self._finish_process()

    def pause(self) -> dict:
        DraftPause(self).execute()
        return self._finish_process(False)

    def restart(self) -> dict:
        DraftRestart(self).execute()
        return self._finish_process()

    def pickup(
        self,
        member_key: str | None = None,
        use_ranking: bool = False,
        auto_draft: bool = True,
    ) -> dict:
        self._draft_values.load_members()
        DraftMember(
            self, member_key=member_key, use_ranking=use_ranking, auto_draft=auto_draft
        ).execute()
        return self._finish_process()

    def _finish_process(self, draft_unsigned_users: bool = True) -> dict:
        self.draft_notice.send()
        data = dict(self._draft_values.division)
        team = self.draft_values.team
        if team is not None:
            data["Teams"] = [team.get("teamNum")]
            if draft_unsigned_users:
                cnt = 0
                self.draft_values.load_members()
                drafting_users = self._draft_values.get_drafting_users()
                while self._draft_unsigned_users(team, drafting_users):
                    team = self.draft_values.team
                    cnt += 1
                if cnt > 0:
                    self.draft_notice.send()

        d = self._draft_values.division
        if d.get("draftStatus") == DraftConstants.DRAFT_STATUS_DRAFTED:
            DraftClose(
                self.db, d["leagueID"], self._user_id, RequestContext.get_datetime()
            ).execute()
        return data

    def _draft_unsigned_users(
        self, team: dict | None, drafting_users: list[int]
    ) -> bool:
        if team is None:
            return False
        user_id = team.get("userID")
        if user_id is None or user_id in drafting_users:
            return False
        DraftMember(self, draft_unsigned=True).execute()
        return True


def start_draft(db: Session, user_id: int, division_id: int) -> dict:
    dh = DraftHelper(db, user_id, division_id)
    return dh.start()


def pause_draft(db: Session, user_id: int, division_id: int) -> dict:
    dh = DraftHelper(db, user_id, division_id)
    return dh.pause()


def restart_draft(db: Session, user_id: int, division_id: int) -> dict:
    dh = DraftHelper(db, user_id, division_id)
    return dh.restart()


def pickup_member(
    db: Session,
    user_id: int,
    division_id: int,
    member_key: str | None = None,
    use_ranking: bool = False,
    auto_draft: bool = True,
) -> dict:
    dh = DraftHelper(db, user_id, division_id)
    return dh.pickup(
        member_key=member_key, use_ranking=use_ranking, auto_draft=auto_draft
    )
