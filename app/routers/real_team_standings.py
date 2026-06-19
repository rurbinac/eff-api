from fastapi import APIRouter, Query, Form, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.context import RequestContext
from app.actions.real_team_standings import RealTeamStandingsReadListAction
from app.utils import JsonApiSerializer

router = APIRouter(tags=["real-team-standings"])


class RealTeamStandingsRequest(BaseModel):
    realCompetitionID: int
    realCompetitionSeasonID: int


@router.post("/eff/eff_api/RealTeamStandings.php")
async def legacy_real_team_standings(
    f: str = Query(...),
    format: str | None = Query("json", alias="_format"),
    type: str | None = Query(None, alias="_type"),
    realCompetitionID: int | None = Form(None),
    realCompetitionSeasonID: int | None = Form(None),
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible RealTeamStandings endpoint."""
    RequestContext.set_datetime()
    try:
        if f == "ReadList":
            items = RealTeamStandingsReadListAction.execute(
                db,
                real_competition_id=realCompetitionID,
                real_competition_season_id=realCompetitionSeasonID
            )
            return {
                "table": "RealTeamStandings",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items]
            }
        else:
            return {"error": f"Unknown function: {f}"}, 400
    finally:
        RequestContext.reset()


@router.get("/api/v1/real_team_standings")
async def rest_real_team_standings(
    payload: RealTeamStandingsRequest,
    db: Session = Depends(get_db),
):
    """REST endpoint for RealTeamStandings ReadList (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        items = RealTeamStandingsReadListAction.execute(
            db,
            real_competition_id=realCompetitionID,
            real_competition_season_id=realCompetitionSeasonID
        )
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='real-team-standings',
            resource_id_key='realTeamStandingID',
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()
