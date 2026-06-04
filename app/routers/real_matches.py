from fastapi import APIRouter, Query, Form, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.context import RequestContext
from app.actions.real_matches import RealMatchesReadListAction

router = APIRouter(tags=["real-matches"])


@router.post("/eff/eff_api/RealMatches.php")
async def legacy_real_matches(
    f: str = Query(...),
    format: str | None = Query("json", alias="_format"),
    type: str | None = Query(None, alias="_type"),
    realCompetitionID: int | None = Form(None),
    realCompetitionSeasonID: int | None = Form(None),
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible RealMatches endpoint."""
    RequestContext.set_datetime()
    try:
        if f == "ReadList":
            items = RealMatchesReadListAction.execute(
                db,
                real_competition_id=realCompetitionID,
                real_competition_season_id=realCompetitionSeasonID
            )
            return {
                "table": "RealMatches",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items]
            }
        else:
            return {"error": f"Unknown function: {f}"}, 400
    finally:
        RequestContext.reset()


@router.post("/api/realmatches/readlist")
async def rest_real_matches(
    realCompetitionID: int,
    realCompetitionSeasonID: int,
    db: Session = Depends(get_db),
):
    """REST endpoint for RealMatches ReadList."""
    RequestContext.set_datetime()
    try:
        items = RealMatchesReadListAction.execute(
            db,
            real_competition_id=realCompetitionID,
            real_competition_season_id=realCompetitionSeasonID
        )
        return items
    finally:
        RequestContext.reset()
