from sqlalchemy.orm import Session

from app.context import RequestContext
from app.services.query import QueryService


class TopEPLAction:
    """Get top EPL teams action."""

    @staticmethod
    def execute(db: Session, limit: int = 4) -> dict:
        """Get top EPL teams and return in legacy format."""
        teams = QueryService.get_top_epl_teams(db, limit)

        return {
            "table": "TopEPL",
            "timestamp": RequestContext.get_datetime_iso(),
            "items": [{"values": {"realTeamShortName": team}} for team in teams]
        }
