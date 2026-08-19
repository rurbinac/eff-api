from fastapi import APIRouter, Form, Query
from pydantic import BaseModel

from app.actions.real_standings import RealStandingsReadListAction
from app.context import RequestContext
from app.database import DbSession
from app.utils import JsonApiSerializer

router = APIRouter(tags=["real-standings"])


class RealStandingsRequest(BaseModel):
    realCompetitionID: int
    realCompetitionMatchDay: int
    divisionID: int | None = None


@router.post("/eff/eff_api/RealStandings.php")
async def legacy_real_standings(
    db: DbSession,
    f: str = Query(...),
    realCompetitionID: int | None = Form(None),
    realCompetitionMatchDay: int | None = Form(None),
    divisionID: int | None = Form(None),
    type: str | None = Form(None, alias="_type"),
):
    """Legacy PHP-compatible RealStandings endpoint."""
    RequestContext.set_datetime()
    try:
        if f == "ReadList":
            items = RealStandingsReadListAction.execute(
                db,
                real_competition_id=realCompetitionID,
                real_competition_match_day=realCompetitionMatchDay,
                division_id=divisionID if type == "byDivisionID" else None,
            )
            return {
                "table": "RealStandings",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items],
            }
        else:
            return {"error": f"Unknown function: {f}"}, 400
    finally:
        RequestContext.reset()


@router.get("/api/v1/real_standings")
async def rest_real_standings(
    payload: RealStandingsRequest,
    db: DbSession,
):
    """REST endpoint for RealStandings ReadList (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        items = RealStandingsReadListAction.execute(
            db,
            real_competition_id=payload.realCompetitionID,
            real_competition_match_day=payload.realCompetitionMatchDay,
            division_id=payload.divisionID,
        )
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='real-standings',
            resource_id_key='realStandingID',
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()
