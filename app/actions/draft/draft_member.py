from collections.abc import Iterator
from datetime import datetime, timedelta

from sqlalchemy import text

from app.actions.draft.draft_base import DraftBase, DraftHelperProtocol
from app.actions.draft.draft_exception import (
    MemberNotAvailableException,
    NotAvailableDraftPositionsException,
    NotAvailableMembersException,
    NotYourTurnException,
)
from app.constants import (
    DraftConstants,
    DraftEvents,
    DraftPositionConstants,
    MatchCreationConstants,
)
from app.utils.match_day_map_keys import div_map_days_map_key, split_map_days_map_key
from app.utils.member_keys import DraftTeamMembers, MKeys


class DraftMember(DraftBase):
    def __init__(
        self,
        dh: DraftHelperProtocol,
        member_key: str | None = None,
        use_ranking: bool = True,
        auto_draft: bool = False,
        draft_unsigned: bool = False,
    ):
        """_summary_

        Args:
            dh (DraftHelperProtocol): _description_
            member_key (str | None, optional): _description_. Defaults to None.
            use_ranking (bool, optional): _description_. Defaults to True.
            auto_draft (bool, optional): _description_. Defaults to False.
            draft_unsigned (bool, optional): _description_. Defaults to False.
        """
        super().__init__(
            dh, DraftConstants.DRAFT_STATUS_DRAFTING, DraftEvents.MEMBER_DRAFTED_EVENT
        )
        self._member_key: str | None = member_key
        self._use_ranking: bool = use_ranking
        self._auto_draft: bool = auto_draft
        self._draft_unsigned: bool = draft_unsigned
        self._timed_out = self._is_timed_out()
        self._selected_key: str | None = None

    def _process_ready(self) -> None:
        super()._process_ready()
        dv = self._dh.draft_values
        team = self.team
        if (
            not self._draft_unsigned
            and not self._timed_out
            and team.get("userID") != self._dh.user_id
        ):
            raise NotYourTurnException()
        dtm = DraftTeamMembers(get_dp=dv.get_dp)
        dtm.unpack(team.get("teamMembers") or "")
        available_positions = dtm.available_dp(draft_lowest=True)

        if not available_positions:
            raise NotAvailableDraftPositionsException()

        for key in self._next_member_key(available_positions):
            dtm.add_member(key)
            if dtm.is_valid():
                self._selected_key = key
                dv.set_member_team_id(key, team.get("teamID"), freeze_values=True)
                return

        raise NotAvailableMembersException()

    def _execute_process(self) -> None:
        """_summary_"""
        d = self.division

        draftingNextTeamOrder = d.get("draftingNextTeamOrder")
        if draftingNextTeamOrder is not None:
            values = self._process_drafting()
        else:
            values = self._process_drafted()
            self.set_team_values(
                values={
                    "matchDayMapKey": values["matchDayMapKey"],
                    "divisionMatches": values["divisionMatches"],
                    "leagueMatches": values["leagueMatches"],
                },
                save_old=True,
            )

        values["draftingFinish"] = self.start_time()
        self.set_division_values(values=values, save_old=True)

    def _process_drafting(self) -> dict:
        """Process the drafting of a single member

        Returns:
            dict: _description_
        """
        d = self.division
        draftingNextTeamOrder = d.get("draftingNextTeamOrder")
        delta = draftingNextTeamOrder - d.get("draftingTeamOrder")
        numTeams = d.get("numTeams")
        draftingTeamOrder = draftingNextTeamOrder
        draftingRound = d.get("draftingRound")
        if delta == 0:
            if draftingNextTeamOrder == 1:
                draftingNextTeamOrder = 2
            else:
                draftingNextTeamOrder = numTeams - 1
            draftingRound += 1
        elif draftingNextTeamOrder > 1 and draftingNextTeamOrder < numTeams:
            draftingNextTeamOrder += delta
        elif DraftPositionConstants.MAX_MEMBER <= draftingRound:
            draftingNextTeamOrder = None
        return {
            "draftStatus": DraftConstants.DRAFT_STATUS_DRAFTING,
            "draftingRound": draftingRound,
            "draftingTeamOrder": draftingTeamOrder,
            "draftingNextTeamOrder": draftingNextTeamOrder,
            "draftingMemberOrder": d.get("draftingMemberOrder") + 1,
            "draftingLimit": self.start_time()
            + timedelta(seconds=DraftConstants.DRAFT_TIME),
        }

    def _process_drafted(self) -> dict:
        """Process the drafting of the last member

        Returns:
            dict: _description_
        """
        d = self.division
        matchDayMapKey = div_map_days_map_key(
            self._dh.db, d.get("numTeams"), rcID=d.get("baseRealCompetitionID")
        )
        _, firstRealCompetitionMatchDay, _, _, _ = split_map_days_map_key(
            matchDayMapKey
        )
        values = {
            "draftStatus": DraftConstants.DRAFT_STATUS_DRAFTED,
            "draftingRound": None,
            "draftingMemberOrder": None,
            "draftingTeamOrder": None,
            "draftingNextTeamOrder": None,
            "matchDayMapKey": matchDayMapKey,
            "draftCompleteDate": self.start_time(),
            "firstRealCompetitionMatchDay": firstRealCompetitionMatchDay,
            "lastRealCompetitionMatchDay": None,
            "divisionMatches": MatchCreationConstants.READY,
            "leagueMatches": MatchCreationConstants.READY,
        }

        return values

    def _terminate_process(self) -> None:
        """_summary_"""
        self._dh.draft_values.save_division(include_curr_team=True)
        self._update_other_teams()
        self._dh.db.commit()
        self._add_notice_info()

    def _is_timed_out(self) -> bool:
        """_summary_

        Returns:
            bool: _description_
        """
        limit = self.division.get("draftingLimit")
        if limit is None:
            return False
        if isinstance(limit, str):
            try:
                limit = datetime.fromisoformat(limit)
            except ValueError:
                return False
        return self.start_time() >= limit

    def _next_member_key(self, available_positions: set[str]) -> Iterator[str]:
        """An iterator that reads members in order

        Args:
            available_positions (set[str]): _description_

        Raises:
            DraftException: _description_

        Yields:
            Iterator[str]: the merber key
        """
        # First try with the selected key
        if self._member_key is not None:
            if self._is_available(self._member_key, available_positions):
                yield self._member_key
            elif (
                not self._auto_draft
                and not self._draft_unsigned
                and not self._timed_out
            ):
                raise MemberNotAvailableException(self._member_key)
        #
        if self._auto_draft or self._draft_unsigned or self._timed_out:
            # Pick up one key automatically
            if self._use_ranking:
                ranking = self.team.get("membersRanking") or ""
                m_keys = MKeys()
                if m_keys.unpack(ranking):
                    for key in m_keys.keys(group=0):
                        if self._is_available(key, available_positions):
                            yield key

            for key in self._dh.draft_values.get_member_keys():
                if self._is_available(key, available_positions):
                    yield key

    def _is_available(self, key: str, available_positions: set[str]) -> bool:
        """Check if a key had no teamID yet and its draft position is into available_positions

        Args:
            key (str): _description_
            available_positions (set[str]): _description_

        Returns:
            bool: _description_
        """
        dv = self._dh.draft_values
        if dv.get_member_team_id(key) is None:
            if dv.get_dp(key) in available_positions:
                return True
        return False

    def _update_other_teams(self) -> None:
        """_summary_"""
        d = self.division
        sql = text("""
            UPDATE `Teams`
               SET `membersRanking` = REPLACE(`membersRanking`, :key, ''),
                   `matchDayMapKey` = :matchDayMapKey,
                   `leagueMatches` = :leagueMatches,
                   `divisionMatches` = :divisionMatches
             WHERE `divisionID` = :divisionID
               AND `teamID` <> :teamID
        """)
        self._dh.db.execute(sql, {
            "key": self._selected_key + MKeys.SUFFIX,
            "matchDayMapKey": d.get("matchDayMapKey"),
            "leagueMatches": d.get("leagueMatches"),
            "divisionMatches": d.get("divisionMatches"),
            "divisionID": d.get("divisionID"),
            "teamID": self._dh.draft_values.get_member_team_id(self._selected_key),
        })

    def _get_event_data(self) -> dict:
        """_summary_

        Returns:
            dict: _description_
        """
        d = self.division
        draftingTeamOrder = d.get("draftingTeamOrder")
        draftingNextTeamOrder = d.get("draftingNextTeamOrder")
        if draftingNextTeamOrder is None:
            next_round = None
        else:
            next_round = d.get("draftingRound")
            if draftingTeamOrder == draftingNextTeamOrder:
                next_round += 1
        data = super()._get_event_data()
        data.update(
            {
                "memberKey": self._selected_key,
                "memberOrder": d.get("draftingMemberOrder"),
                "teamOrder": draftingTeamOrder,
                "round": d.get("draftingRound"),
                "nextTeamOrder": draftingNextTeamOrder,
                "nextRound": next_round,
                "franchiseMembers": d.get("franchiseMembers"),
            }
        )
        return data
