from sqlalchemy.orm import Session

from app.services import QueryService
from app.context import RequestContext


class DivisionNotesReadListAction:
    """Get all notes for a division."""

    @staticmethod
    def execute(db: Session, division_id: int) -> dict:
        """Get notes for a division."""
        request_datetime = RequestContext.get_datetime()

        # Query all notes for division
        rows = QueryService.get_division_notes(db, division_id)

        # Wrap each note in values dict
        items = []
        for row in rows:
            items.append({"values": row})

        return {
            "table": "DivisionNotes",
            "timestamp": request_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "items": items
        }
