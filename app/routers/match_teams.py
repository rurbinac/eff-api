from fastapi import APIRouter, Query, Form, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.context import RequestContext
from app.actions.match_teams import MatchTeamsReadListAction

router = APIRouter(tags=["match-teams"])


@router.post("/eff/eff_api/MatchTeams.php")
async def legacy_match_teams(
    f: str = Query(...),
    format: str | None = Query("json", alias="_format"),
    type: str | None = Query(None, alias="_type"),
    matchID: int | None = Form(None),
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible MatchTeams endpoint."""
    RequestContext.set_datetime()
    try:
        if f == "ReadList":
            items = MatchTeamsReadListAction.execute(db, match_id=matchID)
            return {
                "table": "MatchTeams",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items]
            }
        else:
            return {"error": f"Unknown function: {f}"}, 400
    finally:
        RequestContext.reset()


@router.post("/api/matchteams/readlist")
async def rest_match_teams(
    matchID: int,
    db: Session = Depends(get_db),
):
    """REST endpoint for MatchTeams ReadList."""
    RequestContext.set_datetime()
    try:
        items = MatchTeamsReadListAction.execute(db, match_id=matchID)
        return items
    finally:
        RequestContext.reset()
