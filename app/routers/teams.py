from fastapi import APIRouter, Depends, Request, Query, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.actions.teams import TeamsReadListAction
from app.context import RequestContext

router = APIRouter(tags=["teams"])


@router.post("/eff/eff_api/Teams.php")
async def legacy_teams(
    f: str = Query(..., description="Action name"),
    _format: str | None = Query("json"),
    _type: str | None = Query(None),
    leagueID: int = Form(...),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible endpoint for Teams actions."""
    RequestContext.set_datetime()

    try:
        if f == "ReadList":
            result = TeamsReadListAction.execute(db, leagueID)
            return result
        else:
            return {"error": f"Unknown action: {f}"}, 400
    finally:
        RequestContext.reset()


@router.post("/api/teams/readlist")
def rest_teams(leagueID: int, db: Session = Depends(get_db)):
    """REST endpoint: Get teams for league."""
    RequestContext.set_datetime()
    try:
        result = TeamsReadListAction.execute(db, leagueID)
        # For REST API, return simplified format (no items wrapper)
        return {
            "teams": [item["values"] for item in result["items"]],
            "timestamp": result["timestamp"],
        }
    finally:
        RequestContext.reset()
