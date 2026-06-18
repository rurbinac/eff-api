from sqlalchemy.orm import Session
from app.services.query import QueryService
from app.context import RequestContext


class TopEPLAction:
    """Get top EPL teams action."""

    @staticmethod
    def execute(db: Session, limit: int = 4) -> dict:
        """Get top EPL teams and return in legacy format."""
        teams = QueryService.get_top_epl_teams(db, limit)

        return {
            "table": "TopEPL",
            "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
            "items": [{"values": {"realTeamShortName": team}} for team in teams]
        }
