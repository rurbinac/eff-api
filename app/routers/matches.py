from fastapi import APIRouter, Query, Form, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.context import RequestContext
from app.actions.matches import MatchesReadListAction

router = APIRouter(tags=["matches"])


@router.post("/eff/eff_api/Matches.php")
async def legacy_matches(
    f: str = Query(...),
    format: str | None = Query("json", alias="_format"),
    type: str | None = Query(None, alias="_type"),
    leagueID: int | None = Form(None),
    divisionID: int | None = Form(None),
    teamID: int | None = Form(None),
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible Matches endpoint."""
    RequestContext.set_datetime()
    try:
        if f == "ReadList":
            items = MatchesReadListAction.execute(
                db,
                league_id=leagueID,
                division_id=divisionID,
                team_id=teamID
            )
            return {
                "table": "Matches",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items]
            }
        else:
            return {"error": f"Unknown function: {f}"}, 400
    finally:
        RequestContext.reset()


@router.post("/api/matches/readlist")
async def rest_matches(
    leagueID: int | None = None,
    divisionID: int | None = None,
    teamID: int | None = None,
    db: Session = Depends(get_db),
):
    """REST endpoint for Matches ReadList."""
    RequestContext.set_datetime()
    try:
        items = MatchesReadListAction.execute(
            db,
            league_id=leagueID,
            division_id=divisionID,
            team_id=teamID
        )
        return items
    finally:
        RequestContext.reset()
