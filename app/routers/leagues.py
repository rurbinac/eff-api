from fastapi import APIRouter, Depends, Request, Query, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.actions.leagues import LeaguesReadListAction
from app.context import RequestContext

router = APIRouter(tags=["leagues"])


@router.post("/eff/eff_api/Leagues.php")
async def legacy_leagues(
    f: str = Query(..., description="Action name"),
    format: str | None = Query("json", alias="_format"),
    type: str | None = Query(None, alias="_type"),
    userID: int = Form(...),
    season: int | None = Form(None),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible endpoint for Leagues actions."""
    RequestContext.set_datetime()

    try:
        if f == "ReadList":
            # Get data from action
            items = LeaguesReadListAction.execute(db, userID, season)
            # Format as legacy PHP response
            return {
                "table": "Leagues",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items]
            }
        else:
            return {"error": f"Unknown action: {f}"}
    finally:
        RequestContext.reset()


@router.post("/api/leagues/readlist")
def rest_leagues(userID: int, season: int | None = None, db: Session = Depends(get_db)):
    """REST endpoint: Get leagues for user."""
    RequestContext.set_datetime()
    try:
        # Get data from action and return as REST array
        return LeaguesReadListAction.execute(db, userID, season)
    finally:
        RequestContext.reset()
