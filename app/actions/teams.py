from sqlalchemy.orm import Session

from app.services import QueryService
from app.context import RequestContext


class TeamsReadListAction:
    """Get all teams for a league."""

    @staticmethod
    def execute(db: Session, league_id: int) -> dict:
        """Get teams for a league."""
        request_datetime = RequestContext.get_datetime()

        # Query all teams for league
        rows = QueryService.get_teams_by_league(db, league_id)

        # Wrap each team in values dict
        items = []
        for row in rows:
            items.append({"values": row})

        return {
            "table": "Teams",
            "timestamp": request_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "items": items
        }
