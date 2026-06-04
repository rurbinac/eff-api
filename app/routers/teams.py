from fastapi import APIRouter, Depends, Request, Query, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.actions.teams import TeamsReadListAction
from app.context import RequestContext

router = APIRouter(tags=["teams"])


@router.post("/eff/eff_api/Teams.php")
async def legacy_teams(
    f: str = Query(..., description="Action name"),
    format: str | None = Query("json", alias="_format"),
    type: str | None = Query(None, alias="_type"),
    leagueID: int | None = Form(None),
    divisionID: int | None = Form(None),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible endpoint for Teams actions."""
    RequestContext.set_datetime()

    try:
        if f == "ReadList":
            if type == "byDivisionID":
                items = TeamsReadListAction.execute(db, division_id=divisionID)
            else:
                items = TeamsReadListAction.execute(db, league_id=leagueID)
            return {
                "table": "Teams",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items]
            }
        else:
            return {"error": f"Unknown action: {f}"}, 400
    finally:
        RequestContext.reset()


@router.post("/api/teams/readlist")
def rest_teams(
    leagueID: int | None = None,
    divisionID: int | None = None,
    db: Session = Depends(get_db)
):
    """REST endpoint: Get teams for league or division."""
    RequestContext.set_datetime()
    try:
        items = TeamsReadListAction.execute(db, league_id=leagueID, division_id=divisionID)
        return items
    finally:
        RequestContext.reset()
