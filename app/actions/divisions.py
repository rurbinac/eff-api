from datetime import timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services import QueryService
from app.context import RequestContext
from app.utils import MKeys
from app.models import RealStanding
from fastapi import HTTPException, status


class DivisionsReadListAction:
    """Get all divisions for a league."""

    @staticmethod
    def execute(db: Session, league_id: int) -> list[dict]:
        """Get divisions for a league (pure data, no wrapper)."""
        # Query all divisions for league
        rows = QueryService.get_divisions_by_league(db, league_id)
        # Return pure data (no response wrapper)
        return rows


class DivisionsTransactionsDetailAction:
    """Get transaction details for a division (last 14 days)."""

    @staticmethod
    def _get_added_dropped(row: dict, before_key: str, after_key: str) -> tuple[list[str], list[str]]:
        """Parse member strings and return added and dropped members."""
        members_before_str = row.get(before_key) or ""
        members_after_str = row.get(after_key) or ""

        # Parse using MKeys
        before_keys = MKeys(members_before_str, size=1)
        after_keys = MKeys(members_after_str, size=1)

        before_list = before_keys.get_group(0) if before_keys.is_valid else []
        after_list = after_keys.get_group(0) if after_keys.is_valid else []

        # Calculate added and dropped
        added = list(set(after_list) - set(before_list))
        dropped = list(set(before_list) - set(after_list))

        return added, dropped

    @staticmethod
    def _split_members(row: dict) -> dict:
        """Split transaction members into categories."""
        added, dropped = DivisionsTransactionsDetailAction._get_added_dropped(
            row, "membersBefore", "membersAfter"
        )

        # If no transfer, just return added/dropped
        if row.get("teamMemberTransferID") is None:
            return {
                "added": added,
                "dropped": dropped,
            }

        # Parse other team's changes
        other_added, other_dropped = DivisionsTransactionsDetailAction._get_added_dropped(
            row, "otherMembersBefore", "otherMembersAfter"
        )

        # Calculate sent and received
        sent = list(set(dropped) & set(other_added))
        received = list(set(added) & set(other_dropped))

        return {
            "added": list(set(added) - set(received)),
            "dropped": list(set(dropped) - set(sent)),
            "received": received,
            "sent": sent,
            "otherAdded": list(set(other_added) - set(sent)),
            "otherDropped": list(set(other_dropped) - set(received)),
        }

    @staticmethod
    def _get_member_stats(db: Session, key: str, real_competition_id: int) -> dict | None:
        """Query RealStandings for member stats."""
        try:
            stmt = text("""
                SELECT * FROM `RealStandings`
                WHERE `realTeamMemberKey` = :key
                  AND `realCompetitionID` = :realCompetitionID
                  AND `realCompetitionMatchDay` = 38
                LIMIT 1
            """)
            result = db.execute(stmt, {"key": key, "realCompetitionID": real_competition_id})
            row = result.mappings().first()
            return dict(row) if row else None
        except Exception:
            return None

    @staticmethod
    def execute(db: Session, division_id: int) -> list[dict]:
        """Get transaction details for division in last 14 days (pure data, no wrapper)."""
        # Query transaction logs with database-agnostic date calculation
        stmt = text("""
            SELECT `t1`.`baseRealCompetitionID` AS `realCompetitionID`,
                   `tml1`.`teamMemberLogID`,
                   `tml1`.`teamMemberTransferID`,
                   `tml1`.`leagueID`,
                   `tml1`.`divisionID`,
                   `tml1`.`teamID`,
                   `tml1`.`userID`,
                   `t1`.`teamName`,
                   `tml1`.`requester`,
                   `tml1`.`transactionType`,
                   `tml1`.`membersBefore`,
                   `tml1`.`membersAfter`,
                   `tml2`.`teamID` AS `otherTeamID`,
                   `tml2`.`userID` AS `otherUserID`,
                   `t2`.`teamName` AS `otherTeamName`,
                   `tml2`.`membersBefore` AS `otherMembersBefore`,
                   `tml2`.`membersAfter` AS `otherMembersAfter`,
                   `tml1`.`createdIn` AS `processDate`,
                   `tmt`.`createdIn` AS `requestDate`
            FROM `TeamMemberLog` `tml1`
            LEFT OUTER JOIN `Teams` `t1` ON `tml1`.`teamID` = `t1`.`teamID`
            LEFT OUTER JOIN `TeamMemberTransfers` `tmt` ON `tml1`.`teamMemberTransferID` = `tmt`.`teamMemberTransferID`
            LEFT OUTER JOIN `TeamMemberLog` `tml2` ON `tml2`.`teamMemberTransferID` = `tmt`.`teamMemberTransferID`
            LEFT OUTER JOIN `Teams` `t2` ON `tml2`.`teamID` = `t2`.`teamID`
            WHERE `tml1`.`divisionID` = :divisionID
              AND `tml1`.`createdIn` >= datetime('now', '-14 days')
            ORDER BY `tml1`.`createdIn` DESC
        """)

        results = db.execute(stmt, {"divisionID": division_id})
        rows = [dict(row) for row in results.mappings()]

        members = []
        for row in rows:
            # Remove member string fields
            row.pop("membersBefore", None)
            row.pop("membersAfter", None)
            row.pop("otherMembersBefore", None)
            row.pop("otherMembersAfter", None)

            # Split members by transaction type
            splitted = DivisionsTransactionsDetailAction._split_members(row)

            # For each transaction type and member
            for transaction_type, keys in splitted.items():
                for key in keys:
                    # Get member stats from RealStandings
                    member_stats = DivisionsTransactionsDetailAction._get_member_stats(
                        db, key, row.get("realCompetitionID")
                    )

                    # Create member transaction record
                    member_record = row.copy()
                    member_record["type"] = transaction_type
                    member_record["realTeamMemberKey"] = key

                    # Merge in member stats if found
                    if member_stats:
                        member_record.update(member_stats)

                    members.append(member_record)

        return members
