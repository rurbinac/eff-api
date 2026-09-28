from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.constants import TeamMemberTransfersStatusConstants
from app.guards import require_team_owner
from app.models import TeamMemberTransfers
from app.services import QueryService
from app.utils.rtm_keys import KeyGroups


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
