from fastapi import APIRouter, Depends, Request, Query, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.actions.leagues import LeaguesReadListAction
from app.context import RequestContext

router = APIRouter(tags=["leagues"])


@router.post("/eff/eff_api/Leagues.php")
async def legacy_leagues(
    f: str = Query(..., description="Action name"),
    _format: str | None = Query("json"),
    _type: str | None = Query(None),
    userID: int = Form(...),
    season: int | None = Form(None),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible endpoint for Leagues actions."""
    RequestContext.set_datetime()

    try:
        if f == "ReadList":
            result = LeaguesReadListAction.execute(db, userID, season)
            return result
        else:
            return {"error": f"Unknown action: {f}"}, 400
    finally:
        RequestContext.reset()


@router.post("/api/leagues/readlist")
def rest_leagues(userID: int, season: int | None = None, db: Session = Depends(get_db)):
    """REST endpoint: Get leagues for user."""
    RequestContext.set_datetime()
    try:
        result = LeaguesReadListAction.execute(db, userID, season)
        # For REST API, return a simpler format (no items wrapper)
        return {
            "leagues": [item["values"] for item in result["items"]],
            "timestamp": result["timestamp"],
        }
    finally:
        RequestContext.reset()
