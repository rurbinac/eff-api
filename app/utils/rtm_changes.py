from sqlalchemy import text
from sqlalchemy.orm import Session

from app.constants import (
    TeamMemberLogConstants,
    TeamMemberTransfersStatusConstants,
    WaiversConstants,
)
from app.exceptions import CannotSaveException
from app.guards import require_team, require_team_owner
from app.models import Team, TeamMemberLog, TeamMemberTransfers
from app.utils.dt import utc_now
from app.utils.readers import KeysReader
from app.utils.rtm_keys import KeyGroups, Keys, MemberKeys


def save_drafted_log(db: Session, team: Team) -> None:
    _save_log(db, TeamMemberLogConstants.DRAFTED, team, "")


class RTMChange:
    def __init__(self, db: Session, reader: KeysReader):
        self._db = db
        self._reader: KeysReader = reader
        self._div_cache: dict[str, str] = {}

    def _read_division_keys(
        self, db: Session, team: Team, other_team: Team | None = None
    ) -> Keys:
        rows = (
            db.execute(
                text(
                    "SELECT `teamMembers` FROM `Teams` WHERE `divisionID` = :div AND `teamID` != :tid_1 AND `teamID` != :tid_2"
                ),
                {
                    "div": team.divisionID,
                    "tid_1": team.teamID,
                    "tid_2": team.teamID if other_team is None else other_team.teamID,
                },
            )
            .mappings()
            .all()
        )
        division_keys = Keys(allow_dups=None)
        for row in rows:
            for key in Keys.to_list(row.get("teamMembers") or "") or []:
                division_keys.append(key)
        return division_keys


class AddDrop(RTMChange):
    def __init__(self, db: Session, reader: KeysReader):
        super().__init__(db, reader)

    def execute(self, user_id: int, team: Team, add_drop: Keys) -> None:
        keys_before = team.teamMembers or ""
        members, to_add, to_drop = self._init_keys(team, add_drop)
        if len(to_add) + len(to_drop) == 0:
            return False
        self._check_max(team, len(to_add), len(to_drop))

        if to_add:
            div_keys = self._read_division_keys(self._db, team)
            for key in to_add:
                if key in div_keys:
                    raise CannotSaveException(
                        "teamMembers", f"{key} is already taken in the division"
                    )

        self._reader.load(keys=members + to_add)

        if not members.try_change(to_add, to_drop):
            raise CannotSaveException(
                "teamMembers", "invalid team composition after changes"
            )

        packed = members.pack()
        team.teamMembers = packed
        team.cntAdd += len(to_add)
        team.cntDrop += len(to_drop)
        team.updatedBy = user_id
        team.updatedIn = utc_now()
        _save_log(self._db, TeamMemberLogConstants.ADD_DROP, team, keys_before)
        self._db.commit()

    def _init_keys(
        self, team: Team, add_drop: Keys
    ) -> tuple[MemberKeys, list[str], list[str]]:
        members = MemberKeys(self._reader)
        members.unpack(team.teamMembers)
        to_add, to_drop = members.get_add_drops(add_drop)
        return members, to_add, to_drop

    def _check_max(self, team: Team, add: int, drop: int) -> None:
        if isinstance(WaiversConstants.MAX_ADD, int):
            tot_add = add + team.cntAdd
            if WaiversConstants.MAX_ADD < tot_add:
                raise CannotSaveException(
                    "teamMembers", f"too many adds (max {WaiversConstants.MAX_ADD})"
                )
        if isinstance(WaiversConstants.MAX_DROP, int):
            tot_drop = drop + team.cntDrop
            if WaiversConstants.MAX_DROP < tot_drop:
                raise CannotSaveException(
                    "teamMembers", f"too many drops (max {WaiversConstants.MAX_DROP})"
                )


class Transfer(AddDrop):
    def __init__(self, db: Session, reader: KeysReader):
        super().__init__(db, reader)
        self._team: Team | None = None
        self._other_team: Team | None = None
        self._requested: Keys | None = None
        self._offered: Keys | None = None
        self._members: MemberKeys | None = None
        self._other_members: MemberKeys | None = None
        self._to_add: list[str] | None = None
        self._to_drop: list[str] | None = None
        self._other_to_add: list[str] | None = None
        self._other_to_drop: list[str] | None = None

    def _check_keys(
        self,
        team: Team,
        other_team: Team,
        requested: Keys,
        offered: Keys,
        add_drop: Keys,
        other_add_drop: Keys | None = None,
    ) -> None:
        if team.divisionID != other_team.divisionID:
            raise CannotSaveException("teamMembers", "teams must be in the same division")

        team_set = set(Keys.to_list(team.teamMembers or "") or [])
        other_set = set(Keys.to_list(other_team.teamMembers or "") or [])

        for key in offered:
            if key not in team_set:
                raise CannotSaveException("memberKeys", f"{key} is not in your roster")

        for key in requested:
            if key not in other_set:
                raise CannotSaveException("memberKeys", f"{key} is not in the other team's roster")

        requested_set = set(requested)
        offered_set = set(offered)
        free_adds = [k for k in add_drop if k not in team_set and k not in requested_set]
        other_free_adds = (
            [k for k in other_add_drop if k not in other_set and k not in offered_set]
            if other_add_drop is not None else []
        )
        if free_adds or other_free_adds:
            div_keys = self._read_division_keys(self._db, team, other_team)
            for key in free_adds + other_free_adds:
                if key in div_keys:
                    raise CannotSaveException(
                        "memberKeys", f"{key} is already taken in the division"
                    )

        self._members = MemberKeys(self._reader)
        self._members.unpack(team.teamMembers)
        self._to_add, self._to_drop = self._members.get_add_drops(add_drop)

        if other_add_drop is not None:
            self._other_members = MemberKeys(self._reader)
            self._other_members.unpack(other_team.teamMembers)
            self._other_to_add, self._other_to_drop = self._other_members.get_add_drops(other_add_drop)
            self._reader.load(
                keys=self._members + self._to_add + self._other_members + self._other_to_add
            )
            if not self._members.try_change(self._to_add, self._to_drop):
                raise CannotSaveException("teamMembers", "invalid team composition after transfer")
            if not self._other_members.try_change(self._other_to_add, self._other_to_drop):
                raise CannotSaveException("teamMembers", "invalid team composition after transfer")
        else:
            self._reader.load(keys=self._members + self._to_add)
            if not self._members.try_change(self._to_add, self._to_drop):
                raise CannotSaveException("teamMembers", "invalid team composition after transfer")


class RequestTransfer(Transfer):
    def __init__(self, db: Session, reader: KeysReader):
        super().__init__(db, reader)

    def execute(
        self,
        user_id: int,
        team_id: int,
        other_team_id: int,
        requested: Keys,
        offered: Keys,
        add_drop: Keys,
    ) -> dict:
        team = require_team_owner(self._db, user_id, team_id)
        other_team = require_team(self._db, other_team_id)

        self._check_keys(team, other_team, requested, offered, add_drop)

        member_keys = KeyGroups.DELIM.join(
            [
                requested.pack(),
                offered.pack(),
                add_drop.pack(),
                "",
            ]
        )
        transfer = TeamMemberTransfers(
            teamID=team_id,
            otherTeamID=other_team_id,
            transferStatus=TeamMemberTransfersStatusConstants.REQUESTED,
            memberKeys=member_keys,
            createdIn=utc_now(),
        )
        self._db.add(transfer)
        self._db.commit()
        self._db.refresh(transfer)
        return {
            "teamMemberTransferID": transfer.teamMemberTransferID,
            "teamID": transfer.teamID,
            "otherTeamID": transfer.otherTeamID,
            "transferStatus": transfer.transferStatus,
            "memberKeys": transfer.memberKeys,
        }


class AcceptTransfer(Transfer):
    def __init__(self, db: Session, reader: KeysReader):
        super().__init__(db, reader)

    def execute(
        self,
        user_id: int,
        team: Team,
        other_team: Team,
        other_add_drop: Keys,
        transfer: TeamMemberTransfers,
    ) -> None:
        keys_before = team.teamMembers or ""
        other_keys_before = other_team.teamMembers or ""
        transfer_keys = KeyGroups.create(transfer.memberKeys or "")
        requested = transfer_keys[0] if len(transfer_keys) > 0 else Keys()
        offered = transfer_keys[1] if len(transfer_keys) > 1 else Keys()
        team_add_drop = transfer_keys[2] if len(transfer_keys) > 2 else Keys()

        self._check_keys(team, other_team, requested, offered, team_add_drop, other_add_drop)

        team.teamMembers = self._members.pack()
        team.cntAdd += len(self._to_add)
        team.cntDrop += len(self._to_drop)
        team.updatedBy = user_id
        team.updatedIn = utc_now()

        other_team.teamMembers = self._other_members.pack()
        other_team.cntAdd += len(self._other_to_add)
        other_team.cntDrop += len(self._other_to_drop)
        other_team.updatedBy = user_id
        other_team.updatedIn = utc_now()

        groups = [
            transfer_keys[i].pack() if i < len(transfer_keys) else "" for i in range(3)
        ]
        groups.append(other_add_drop.pack())
        transfer.memberKeys = KeyGroups.DELIM.join(groups)
        transfer.transferStatus = TeamMemberTransfersStatusConstants.ACCEPTED
        transfer.updatedIn = utc_now()
        _save_log(
            self._db,
            TeamMemberLogConstants.TRANSFER_SOURCE,
            team,
            keys_before,
            transfer_id=transfer.teamMemberTransferID,
            other_team=other_team,
            other_keys_before=other_keys_before,
        )
        self._db.commit()


class SettleWaivers(AddDrop):
    def __init__(self, db: Session, reader: KeysReader):
        super().__init__(db, reader)

    def execute(self, division_id: int) -> bool:
        pass


def _save_log(
    db: Session,
    transaction_type: int,
    team: Team,
    keys_before: str,
    transfer_id: int | None = None,
    other_team: Team | None = None,
    other_keys_before: str | None = None,
) -> None:
    db.add(
        TeamMemberLog(
            teamMemberTransferID=transfer_id,
            leagueID=team.leagueID,
            divisionID=team.divisionID,
            teamID=team.teamID,
            userID=team.userID,
            requester=1,
            transactionType=transaction_type,
            membersBefore=keys_before,
            membersAfter=team.teamMembers,
            createdIn=utc_now(),
        )
    )
    if (
        transaction_type == TeamMemberLogConstants.TRANSFER_SOURCE
        and other_team is not None
    ):
        db.add(
            TeamMemberLog(
                teamMemberTransferID=transfer_id,
                leagueID=other_team.leagueID,
                divisionID=other_team.divisionID,
                teamID=other_team.teamID,
                userID=other_team.userID,
                requester=0,
                transactionType=TeamMemberLogConstants.TRANSFER_TARGET,
                membersBefore=other_keys_before,
                membersAfter=other_team.teamMembers,
                createdIn=utc_now(),
            )
        )
