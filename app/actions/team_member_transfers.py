from sqlalchemy import text
from sqlalchemy.orm import Session

from app.guards import require_team_owner
from app.utils.member_keys import KeyGroups


class TeamMemberTransfersGetPendingByTeamIDAction:
    """Get pending member transfers for a team."""

    STATUS_REQUESTED = 1

    @staticmethod
    def execute(db: Session, team_id: int, user_id: int) -> list[dict]:
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
        # Query TeamMemberTransfers for pending transfers
        tmt_stmt = text("""
            SELECT *
            FROM `TeamMemberTransfers`
            WHERE `transferStatus` = :status
              AND (`teamID` = :teamID OR `otherTeamID` = :teamID)
        """)
        tmt_result = db.execute(tmt_stmt, {
            "status": TeamMemberTransfersGetPendingByTeamIDAction.STATUS_REQUESTED,
            "teamID": team_id
        })
        transfers = [dict(row) for row in tmt_result.mappings()]

        items = []
        field_names = ['requested', 'offered', 'addDrop', 'otherAddDrop']

        for transfer_row in transfers:
            member_keys_str = transfer_row.get('memberKeys') or ""
            transfer_row.pop('memberKeys', None)
            kg = KeyGroups.unpack(member_keys_str)

            if not kg:
                continue

            for g, group in enumerate(kg):
                field_name = field_names[g] if g < len(field_names) else None
                if not field_name:
                    continue

                for key in group:
                    # Query RealTeamMembers for this member
                    rtm_stmt = text("""
                        SELECT *
                        FROM `RealTeamMembers`
                        WHERE `realTeamMemberKey` = :key
                    """)
                    rtm_result = db.execute(rtm_stmt, {"key": key})
                    member_row = rtm_result.mappings().first()

                    # Build the combined row
                    combined_row = transfer_row.copy()

                    if member_row:
                        combined_row.update(dict(member_row))
                    else:
                        # If member not found, include just the key
                        combined_row['realTeamMemberKey'] = key

                    # Add memberType field
                    combined_row['memberType'] = field_name

                    items.append(combined_row)

        return items
