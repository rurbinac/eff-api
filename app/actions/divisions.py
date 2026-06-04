from sqlalchemy.orm import Session

from app.services import QueryService
from app.context import RequestContext
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
