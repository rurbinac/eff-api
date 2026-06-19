from fastapi import APIRouter, Query, Form, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.context import RequestContext
from app.actions.real_standings import RealStandingsReadListAction
from app.utils import JsonApiSerializer

router = APIRouter(tags=["real-standings"])


class RealStandingsRequest(BaseModel):
    realCompetitionID: int
    realCompetitionSeasonID: int


@router.post("/eff/eff_api/RealStandings.php")
async def legacy_real_standings(
    f: str = Query(...),
    format: str | None = Query("json", alias="_format"),
    type: str | None = Query(None, alias="_type"),
    realCompetitionID: int | None = Form(None),
    realCompetitionSeasonID: int | None = Form(None),
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible RealStandings endpoint."""
    RequestContext.set_datetime()
    try:
        if f == "ReadList":
            items = RealStandingsReadListAction.execute(
                db,
                real_competition_id=realCompetitionID,
                real_competition_season_id=realCompetitionSeasonID
            )
            return {
                "table": "RealStandings",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items]
            }
        else:
            return {"error": f"Unknown function: {f}"}, 400
    finally:
        RequestContext.reset()


@router.get("/api/v1/real_standings")
async def rest_real_standings(
    payload: RealStandingsRequest,
    db: Session = Depends(get_db),
):
    """REST endpoint for RealStandings ReadList (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        items = RealStandingsReadListAction.execute(
            db,
            real_competition_id=realCompetitionID,
            real_competition_season_id=realCompetitionSeasonID
        )
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='real-standings',
            resource_id_key='realStandingID',
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()
