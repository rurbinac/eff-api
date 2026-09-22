from sqlalchemy.orm import Session

from app.guards import require_league_member
from app.services import QueryService


class DivisionNotesReadListAction:
    """Get all notes for a division."""

    @staticmethod
    def execute(db: Session, division_id: int, user_id: int) -> list[dict]:
        """Get notes for a division."""
        require_league_member(db, user_id, division_id=division_id)
        # Query all notes for division
        rows = QueryService.get_division_notes(db, division_id)

        # Wrap each note in values dict
        items = []
        for row in rows:
            items.append({"values": row})

        return items
