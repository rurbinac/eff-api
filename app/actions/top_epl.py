from sqlalchemy.orm import Session

from app.services.query import QueryService


class TopEPLAction:
    """Get top EPL teams action."""

    @staticmethod
    def execute(db: Session, limit: int = 4) -> list[dict]:
        teams = QueryService.get_top_epl_teams(db, limit)
        return [{"realTeamShortName": team} for team in teams]
