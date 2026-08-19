from fastapi import APIRouter, Form, Query
from pydantic import BaseModel

from app.actions.real_team_standings import RealTeamStandingsReadListAction
from app.context import RequestContext
from app.database import DbSession
from app.utils import JsonApiSerializer

router = APIRouter(tags=["real-team-standings"])


class RealTeamStandingsRequest(BaseModel):
    realCompetitionID: int
    realCompetitionMatchDay: int


@router.post("/eff/eff_api/RealTeamStandings.php")
async def legacy_real_team_standings(
    db: DbSession,
    f: str = Query(...),
    realCompetitionID: int | None = Form(None),
    realCompetitionMatchDay: int | None = Form(None),
):
    """Legacy PHP-compatible RealTeamStandings endpoint."""
    RequestContext.set_datetime()
    try:
        if f == "ReadList":
            items = RealTeamStandingsReadListAction.execute(
                db,
                real_competition_id=realCompetitionID,
                real_competition_match_day=realCompetitionMatchDay,
            )
            return {
                "table": "RealTeamStandings",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items],
            }
        else:
            return {"error": f"Unknown function: {f}"}, 400
    finally:
        RequestContext.reset()


@router.get("/api/v1/real_team_standings")
async def rest_real_team_standings(
    payload: RealTeamStandingsRequest,
    db: DbSession,
):
    """REST endpoint for RealTeamStandings ReadList (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        items = RealTeamStandingsReadListAction.execute(
            db,
            real_competition_id=payload.realCompetitionID,
            real_competition_match_day=payload.realCompetitionMatchDay,
        )
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='real-team-standings',
            resource_id_key='realTeamStandingID',
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()
