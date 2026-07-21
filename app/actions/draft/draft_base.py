from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Protocol

from sqlalchemy.orm import Session

from app.actions.draft.draft_exception import (
    CannotDraftYetException,
    DraftStatusException,
    NotCommisionerException,
)
from app.actions.draft.draft_notice import DraftNotice
from app.actions.draft.draft_values import DraftValues
from app.constants import DraftConstants, DraftEvents
from app.context import RequestContext


class DraftHelperProtocol(Protocol):
    """_summary_

    Args:
        Protocol (_type_): _description_
    """

    @property
    def db(self) -> Session: ...

    @property
    def user_id(self) -> int: ...

    @property
    def draft_values(self) -> DraftValues: ...

    @property
    def draft_notice(self) -> DraftNotice: ...


class DraftBase(ABC):
    """Base class for draft actions"""

    def __init__(
        self, dh: DraftHelperProtocol, valid_draft_status: int, event_name: str
    ):
        """Initialization

        Args:
            dh (DraftHelperProtocol): a DraftHelper
            valid_draft_status (int): the draftStatus that is valid
            event_name (str): the pusher event name
        """
        self._dh = dh
        self._valid_draft_status: int = valid_draft_status
        self._event_name: str = event_name

    @property
    def division(self) -> dict:
        """_summary_

        Returns:
            dict: _description_
        """
        return self._dh.draft_values.division

    @property
    def old_division(self) -> dict:
        """_summary_

        Returns:
            dict: _description_
        """
        return self._dh.draft_values.old_division

    def set_division_values(
        self, values: dict[str, Any], save_old: bool = False
    ) -> None:
        """_summary_

        Args:
            values (dict[str, Any]): _description_
            save_old (bool, optional): _description_. Defaults to False.
        """
        self._dh.draft_values.set_division_values(values, save_old)

    def freeze_division_values(self, *names: str) -> None:
        """_summary_"""
        self._dh.draft_values.freeze_division_values(*names)

    @property
    def team(self) -> dict | None:
        """_summary_

        Returns:
            dict | None: _description_
        """
        return self._dh.draft_values.team

    @property
    def old_team(self) -> dict:
        """_summary_

        Returns:
            dict: _description_
        """
        return self._dh.draft_values.old_team

    def set_team_values(self, values: dict[str, Any], save_old: bool = False) -> None:
        """_summary_

        Args:
            values (dict[str, Any]): _description_
            save_old (bool, optional): _description_. Defaults to False.
        """
        self._dh.draft_values.set_team_values(values, save_old)

    def freeze_team_values(self, *names: str) -> None:
        """_summary_"""
        self._dh.draft_values.freeze_team_values(*names)

    @property
    def teams(self) -> list[dict]:
        """_summary_

        Returns:
            list[dict]: _description_
        """
        return self._dh.draft_values.teams

    def start_time(self) -> datetime:
        """_summary_

        Returns:
            datetime: _description_
        """
        return RequestContext.get_datetime()

    def execute(self) -> None:
        """_summary_"""
        if self.division.get("draftStatus") != DraftConstants.DRAFT_STATUS_DRAFTED:
            self._process_ready()
            self._execute_process()
            self._terminate_process()

    def _process_ready(self) -> None:
        """_summary_

        Raises:
            DraftStatusException: _description_
        """
        draftStatus = self.division.get("draftStatus")
        if draftStatus != self._valid_draft_status:
            raise DraftStatusException(draftStatus)

    @abstractmethod
    def _execute_process(self) -> None: ...

    @abstractmethod
    def _terminate_process(self) -> None: ...

    def _get_event_data(self) -> dict:
        """_summary_

        Returns:
            dict: _description_
        """
        d = self.division
        return {
            "startTime": d.get("draftingStart"),
            "currTime": self.start_time(),
            "expireTime": d.get("draftingLimit"),
        }

    def _add_notice_info(self) -> None:
        """_summary_"""
        self._dh.draft_notice.add_info(self._event_name, self._get_event_data())


class DraftCommand(DraftBase, ABC):
    """Base for commissioner-triggered draft commands that write to the DB."""

    def _process_ready(self) -> None:
        """_summary_

        Raises:
            NotCommisionerException: _description_
        """
        super()._process_ready()
        # Check if the current user is a commissioner
        if self.division.get("commissionerID") == self._dh.user_id:
            return
        for t in self.teams:
            if t.get("isCommissioner") and t.get("userID") == self._dh.user_id:
                return
        raise NotCommisionerException()

    def _terminate_process(self) -> None:
        """_summary_"""
        self._dh.draft_values.save_division()
        self._dh.db.commit()
        self._add_notice_info()

    def _get_event_data(self) -> dict:
        """_summary_

        Returns:
            dict: _description_
        """
        d = self.division
        data = super()._get_event_data()
        data.update(
            {
                "memberOrder": d.get("draftingMemberOrder"),
                "teamOrder": d.get("draftingTeamOrder"),
                "round": d.get("draftingRound"),
                "franchiseMembers": d.get("franchiseMembers"),
            }
        )
        return data


class DraftStart(DraftCommand):
    def __init__(self, dh: DraftHelperProtocol):
        """_summary_

        Args:
            dh (DraftHelperProtocol): _description_
        """
        super().__init__(
            dh, DraftConstants.DRAFT_STATUS_NOT_DRAFTED, DraftEvents.DRAFT_START_EVENT
        )

    def _process_ready(self) -> None:
        """_summary_

        Raises:
            CannotDraftYetException: _description_
        """
        super()._process_ready()
        if self.division.get("availableTeams", 0) != 0:
            raise CannotDraftYetException()

    def _execute_process(self) -> None:
        """_summary_
        """
        now = self.start_time()
        draftTime = DraftConstants.DRAFT_TIME
        self.set_division_values(
            {
                "draftStatus": DraftConstants.DRAFT_STATUS_DRAFTING,
                "draftingStart": now,
                "draftingFinish": now,
                "draftingLimit": now + timedelta(seconds=draftTime),
                "draftingRound": 1,
                "draftingMemberOrder": 1,
                "draftingTeamOrder": 1,
                "draftingNextTeamOrder": 2,
                "draftTime": draftTime,
                "franchiseMembers": None,
            },
            save_old=True,
        )


class DraftPause(DraftCommand):
    def __init__(self, dh: DraftHelperProtocol):
        """_summary_

        Args:
            dh (DraftHelperProtocol): _description_
        """
        super().__init__(
            dh, DraftConstants.DRAFT_STATUS_DRAFTING, DraftEvents.DRAFT_PAUSE_EVENT
        )

    def _execute_process(self) -> None:
        """_summary_
        """
        self.set_division_values(
            {
                "draftStatus": DraftConstants.DRAFT_STATUS_PAUSED,
                "draftingFinish": self.start_time(),
            },
            save_old=True,
        )


class DraftRestart(DraftCommand):
    def __init__(self, dh: DraftHelperProtocol):
        """_summary_

        Args:
            dh (DraftHelperProtocol): _description_
        """
        super().__init__(
            dh, DraftConstants.DRAFT_STATUS_PAUSED, DraftEvents.DRAFT_START_EVENT
        )

    def _execute_process(self) -> None:
        now = self.start_time()
        d = self.division
        drafting_finish = _to_datetime(d.get("draftingFinish"))
        drafting_limit = _to_datetime(d.get("draftingLimit"))
        if drafting_finish and drafting_limit:
            draft_time = int((drafting_limit - drafting_finish).total_seconds())
        else:
            draft_time = d.get("draftTime", DraftConstants.DRAFT_TIME)
        self.set_division_values(
            {
                "draftStatus": DraftConstants.DRAFT_STATUS_DRAFTING,
                "draftingStart": now,
                "draftingFinish": now,
                "draftingLimit": now + timedelta(seconds=draft_time),
            },
            save_old=True,
        )


def _to_datetime(value: Any) -> datetime | None:
    """_summary_

    Args:
        value (Any): _description_

    Returns:
        datetime | None: _description_
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None
