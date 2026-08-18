from fastapi import APIRouter, Form, Query
from pydantic import BaseModel

from app.actions.real_matches import RealMatchesReadListAction
from app.context import RequestContext
from app.database import DbSession
from app.utils import JsonApiSerializer

router = APIRouter(tags=["real-matches"])


class RealMatchesRequest(BaseModel):
    realCompetitionID: int
    realCompetitionSeasonID: int


@router.post("/eff/eff_api/RealMatches.php")
async def legacy_real_matches(
    db: DbSession,
    f: str = Query(...),
    realCompetitionID: int | None = Form(None),
    realCompetitionMatchDay: int | None = Form(None),
):
    """Legacy PHP-compatible RealMatches endpoint."""
    RequestContext.set_datetime()
    try:
        if f == "ReadList":
            items = RealMatchesReadListAction.execute(
                db,
                real_competition_id=realCompetitionID,
                real_competition_match_day=realCompetitionMatchDay,
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


@router.get("/api/v1/real_matches")
async def rest_real_matches(
    payload: RealMatchesRequest,
    db: DbSession,
):
    """REST endpoint for RealMatches ReadList (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        items = RealMatchesReadListAction.execute(
            db,
            real_competition_id=payload.realCompetitionID,
            real_competition_season_id=payload.realCompetitionSeasonID,
        )
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='real-matches',
            resource_id_key='realMatchID',
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()
