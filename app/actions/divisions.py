from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.guards import (
    require_division,
    require_league_commissioner,
    require_league_member,
)
from app.services import QueryService
from app.utils.dt import to_iso, utc_now
from app.utils.member_keys import Keys


class DivisionsReadListAction:
    """Get all divisions for a league."""

    @staticmethod
    def execute(db: Session, league_id: int) -> list[dict]:
        """Get divisions for a league (pure data, no wrapper)."""
        return QueryService.get_divisions_by_league(db, league_id)


class DivisionsUpdateAction:
    """Update editable division settings (commissioner only)."""

    @staticmethod
    def execute(
        db: Session,
        division_id: int,
        user_id: int,
        draft_type: str | None = None,
        draft_date: datetime | None = None,
        draft_complete_date: datetime | None = None,
    ) -> dict:

        division = require_division(db, division_id)
        require_league_commissioner(db, user_id, division=division)

        if draft_type is not None:
            division.draftType = draft_type
        if draft_date is not None:
            division.draftDate = draft_date
        if draft_complete_date is not None:
            division.draftCompleteDate = draft_complete_date

        division.updatedBy = user_id
        division.updatedIn = utc_now()
        db.commit()
        db.refresh(division)

        return {
            "divisionID": division.divisionID,
            "draftType": division.draftType,
            "draftDate": to_iso(division.draftDate),
            "draftCompleteDate": to_iso(division.draftCompleteDate),
            "updatedBy": division.updatedBy,
            "updatedIn": to_iso(division.updatedIn),
        }


class DivisionsTransactionsDetailAction:
    """Get transaction details for a division (last 14 days)."""

    @staticmethod
    def execute(db: Session, division_id: int, user_id: int) -> list[dict]:
        """Get transaction details for division in last 14 days (pure data, no wrapper)."""
        require_league_member(db, user_id, division_id=division_id)
        # Query transaction logs with database-agnostic date calculation
        rows = DivisionsTransactionsDetailAction._read_TeamMemberLog(db, division_id)

        members = []
        for row in rows:
            # Split members by transaction type (must read before popping)
            splitted = DivisionsTransactionsDetailAction._split_members(row)

            # Remove member string fields
            row.pop("membersBefore", None)
            row.pop("membersAfter", None)
            row.pop("otherMembersBefore", None)
            row.pop("otherMembersAfter", None)

            stats = DivisionsTransactionsDetailAction._get_member_stats(
                db, row.get("realCompetitionID"), splitted.pop("all")
            )

            # For each transaction type and member
            for transaction_type, keys in splitted.items():
                for key in keys:
                    member_record = row.copy()
                    member_record["type"] = transaction_type
                    member_record["realTeamMemberKey"] = key
                    member_stats = stats.get(key)
                    if member_stats:
                        member_record.update(member_stats)
                    members.append(member_record)

        return members

    @staticmethod
    def _read_TeamMemberLog(db: Session, division_id: int) -> list[dict]:
        results = db.execute(
            text("""
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
              AND `tml1`.`createdIn` >= NOW() - INTERVAL 14 DAY
            ORDER BY `tml1`.`createdIn` DESC
        """),
            {"divisionID": division_id},
        )
        return [dict(row) for row in results.mappings()]

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
                "all": list(set(added) | set(dropped)),
            }

        # Parse other team's changes
        other_added, other_dropped = (
            DivisionsTransactionsDetailAction._get_added_dropped(
                row, "otherMembersBefore", "otherMembersAfter"
            )
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
            "all": list(
                set(added) | set(dropped) | set(other_added) | set(other_dropped)
            ),
        }

    @staticmethod
    def _get_added_dropped(
        row: dict, before_key: str, after_key: str
    ) -> tuple[list[str], list[str]]:
        """Parse member strings and return added and dropped members."""
        members_before_str = row.get(before_key) or ""
        members_after_str = row.get(after_key) or ""

        before_list = Keys.to_list(members_before_str) or []
        after_list = Keys.to_list(members_after_str) or []

        # Calculate added and dropped
        added = list(set(after_list) - set(before_list))
        dropped = list(set(before_list) - set(after_list))

        return added, dropped

    @staticmethod
    def _get_member_stats(
        db: Session, real_competition_id: int, keys: list[str]
    ) -> dict[str, dict]:
        """Query RealStandings for all keys in one query; returns dict keyed by realTeamMemberKey."""
        if not keys:
            return {}
        try:
            placeholders = ", ".join(f":key_{i}" for i in range(len(keys)))
            params = {f"key_{i}": k for i, k in enumerate(keys)}
            params["realCompetitionID"] = real_competition_id
            rows = (
                db.execute(
                    text(f"""
                     SELECT *
                        FROM `RealStandings`
                        WHERE `realTeamMemberKey` IN ({placeholders})
                          AND `realCompetitionID` = :realCompetitionID
                          AND `realCompetitionID` = `baseRealCompetitionID`
                          AND `realCompetitionMatchDay` = `realCompetitionLastMatchDay`
                """),
                    params,
                )
                .mappings()
                .all()
            )
            return {row["realTeamMemberKey"]: dict(row) for row in rows}
        except Exception:  # noqa: BLE001
            return {}
