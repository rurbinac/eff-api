from fastapi import APIRouter, Query, Form, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.context import RequestContext
from app.actions.team_standings import TeamStandingsReadListAction
from app.utils import JsonApiSerializer

router = APIRouter(tags=["team-standings"])


class TeamStandingsRequest(BaseModel):
    teamID: int


@router.post("/eff/eff_api/TeamStandings.php")
async def legacy_team_standings(
    f: str = Query(...),
    format: str | None = Query("json", alias="_format"),
    type: str | None = Query(None, alias="_type"),
    teamID: int | None = Form(None),
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible TeamStandings endpoint."""
    RequestContext.set_datetime()
    try:
        if f == "ReadList":
            items = TeamStandingsReadListAction.execute(db, team_id=teamID)
            return {
                "table": "TeamStandings",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items]
            }
        else:
            return {"error": f"Unknown function: {f}"}, 400
    finally:
        RequestContext.reset()


@router.post("/api/teamstandings/readlist")
async def rest_team_standings(
    payload: TeamStandingsRequest,
    db: Session = Depends(get_db),
):
    """REST endpoint for TeamStandings ReadList (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        items = TeamStandingsReadListAction.execute(db, team_id=payload.teamID)
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='team-standings',
            resource_id_key='teamStandingID',
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()
