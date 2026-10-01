from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.actions.teams import TeamsAddAndDropMembersAction
from app.constants import TeamMemberTransfersStatusConstants
from app.exceptions import NotFoundException
from app.guards import require_team_owner
from app.models import TeamMemberTransfers
from app.services import QueryService
from app.utils.dt import utc_now
from app.utils.rtm_keys import KeyGroups, Keys


class TeamMemberTransfersGetPendingByTeamIDAction:
    """Get pending member transfers for a team."""

    @staticmethod
    def execute(db: Session, user_id: int, team_id: int) -> list[dict]:
        """
        Get pending member transfers for a team (as requester or recipient).
        Returns transfer details with member stats and transfer type.

        Args:
            db: Database session
            team_id: Filter by teamID (requesting or receiving team)

        Returns:
            List of transfer records with member details and memberType field
        """
        require_team_owner(db, user_id, team_id=team_id)
        stmt = (
            select(
                TeamMemberTransfers.teamMemberTransferID,
                TeamMemberTransfers.teamID,
                TeamMemberTransfers.otherTeamID,
                TeamMemberTransfers.transferStatus,
                TeamMemberTransfers.memberKeys,
                TeamMemberTransfers.createdIn,
                TeamMemberTransfers.updatedIn,
            )
            .where(
                TeamMemberTransfers.transferStatus == TeamMemberTransfersStatusConstants.REQUESTED,
                or_(
                    TeamMemberTransfers.teamID == team_id,
                    TeamMemberTransfers.otherTeamID == team_id,
                ),
            )
        )
        transfers = [dict(row) for row in db.execute(stmt).mappings().all()]

        field_names = ['requested', 'offered', 'addDrop', 'otherAddDrop']

        # Collect all keys across all transfers for a single batch fetch
        all_keys: list[str] = []
        parsed: list[tuple[dict, list | None]] = []
        for transfer_row in transfers:
            member_keys_str = transfer_row.pop('memberKeys', None) or ""
            kg = KeyGroups.to_list(member_keys_str)
            parsed.append((transfer_row, kg))
            if kg:
                for group in kg:
                    all_keys.extend(group)

        members_by_key = QueryService.get_real_team_members_by_keys(db, all_keys)

        items = []
        for transfer_row, kg in parsed:
            if not kg:
                continue
            for g, group in enumerate(kg):
                field_name = field_names[g] if g < len(field_names) else None
                if not field_name:
                    continue
                for key in group:
                    combined_row = transfer_row.copy()
                    member = members_by_key.get(key)
                    if member:
                        combined_row.update(member)
                    else:
                        combined_row['realTeamMemberKey'] = key
                    combined_row['memberType'] = field_name
                    items.append(combined_row)

        return items


class TeamMemberTransfersRequestAction:
    """Create a new transfer request (requesting team owner)."""

    @staticmethod
    def execute(
        db: Session,
        user_id: int,
        team_id: int,
        other_team_id: int,
        requested: Keys,
        offered: Keys,
        add_drop: Keys,
    ) -> dict:
        require_team_owner(db, user_id, team_id)
        member_keys = KeyGroups.DELIM.join([
            requested.pack(),
            offered.pack(),
            add_drop.pack(),
            "",
        ])
        transfer = TeamMemberTransfers(
            teamID=team_id,
            otherTeamID=other_team_id,
            transferStatus=TeamMemberTransfersStatusConstants.REQUESTED,
            memberKeys=member_keys,
            createdIn=utc_now(),
        )
        db.add(transfer)
        db.commit()
        db.refresh(transfer)
        return {
            "teamMemberTransferID": transfer.teamMemberTransferID,
            "teamID": transfer.teamID,
            "otherTeamID": transfer.otherTeamID,
            "transferStatus": transfer.transferStatus,
            "memberKeys": transfer.memberKeys,
        }


def _require_transfer(db: Session, transfer_id: int) -> TeamMemberTransfers:
    transfer = db.get(TeamMemberTransfers, transfer_id)
    if transfer is None:
        raise NotFoundException(object_name="TeamMemberTransfer", object_id=transfer_id)
    if transfer.transferStatus != TeamMemberTransfersStatusConstants.REQUESTED:
        raise NotFoundException(object_name="TeamMemberTransfer", object_id=transfer_id)
    return transfer


class TeamMemberTransfersAcceptAction:
    """Accept a pending transfer (recipient team owner). Applies addDrop to the accepting team."""

    @staticmethod
    def execute(db: Session, transfer_id: int, user_id: int, add_drop: Keys) -> dict:
        transfer = _require_transfer(db, transfer_id)
        team = db.query(Team).filter(Team.teamID == transfer.teamID).first()
        other_team = require_team_owner(db, user_id, transfer.otherTeamID)
        team_members = TeamsAddAndDropMembersAction._calc_team_members(db, team, add_drop)
        TeamsAddAndDropMembersAction._check_team_members(db, team_members)
        team.teamMembers = team_members.pack()
        team.updatedBy = user_id
        team.updatedIn = utc_now()
        transfer.transferStatus = TeamMemberTransfersStatusConstants.ACCEPTED
        transfer.updatedIn = utc_now()
        db.commit()
        return {"teamMemberTransferID": transfer.teamMemberTransferID, "transferStatus": transfer.transferStatus}


class TeamMemberTransfersRejectAction:
    """Reject a pending transfer (recipient team owner)."""

    @staticmethod
    def execute(db: Session, transfer_id: int, user_id: int) -> dict:
        transfer = _require_transfer(db, transfer_id)
        require_team_owner(db, user_id, transfer.otherTeamID)
        transfer.transferStatus = TeamMemberTransfersStatusConstants.REJECTED
        transfer.updatedIn = utc_now()
        db.commit()
        return {"teamMemberTransferID": transfer.teamMemberTransferID, "transferStatus": transfer.transferStatus}


class TeamMemberTransfersWithdrawAction:
    """Withdraw a pending transfer (requesting team owner)."""

    @staticmethod
    def execute(db: Session, transfer_id: int, user_id: int) -> dict:
        transfer = _require_transfer(db, transfer_id)
        require_team_owner(db, user_id, transfer.teamID)
        transfer.transferStatus = TeamMemberTransfersStatusConstants.WITHDRAWN
        transfer.updatedIn = utc_now()
        db.commit()
        return {"teamMemberTransferID": transfer.teamMemberTransferID, "transferStatus": transfer.transferStatus}
