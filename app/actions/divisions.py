from sqlalchemy.orm import Session

from app.services import QueryService
from app.context import RequestContext
from fastapi import HTTPException, status


class DivisionsReadListAction:
    """Get all divisions for a league."""

    @staticmethod
    def execute(db: Session, league_id: int) -> dict:
        """Get divisions for a league."""
        request_datetime = RequestContext.get_datetime()

        # Query all divisions for league
        rows = QueryService.get_divisions_by_league(db, league_id)

        # Wrap each division in values dict
        items = []
        for row in rows:
            items.append({"values": row})

        return {
            "table": "Divisions",
            "timestamp": request_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "items": items
        }
