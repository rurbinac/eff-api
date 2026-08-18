from fastapi import APIRouter, Form, Query
from pydantic import BaseModel

from app.actions.team_standings import TeamStandingsReadListAction
from app.context import RequestContext
from app.database import CurrentUser, DbSession
from app.utils import JsonApiSerializer

router = APIRouter(tags=["team-standings"])


class TeamStandingsRequest(BaseModel):
    leagueID: int | None = None
    teamID: int | None = None


@router.post("/eff/eff_api/TeamStandings.php")
async def legacy_team_standings(
    db: DbSession,
    current_user: CurrentUser,
    f: str = Query(...),
    teamID: int | None = Form(None),
    leagueID: int | None = Form(None),
):
    """Legacy PHP-compatible TeamStandings endpoint."""
    RequestContext.set_datetime()
    try:
        if f == "ReadList":
            items = TeamStandingsReadListAction.execute(db, user_id=current_user, team_id=teamID, league_id=leagueID)
            return {
                "table": "TeamStandings",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items]
            }
        else:
            return {"error": f"Unknown function: {f}"}, 400
    finally:
        RequestContext.reset()


@router.get("/api/v1/team_standings")
async def rest_team_standings(
    db: DbSession,
    current_user: CurrentUser,
    payload: TeamStandingsRequest,
):
    """REST endpoint for TeamStandings ReadList (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        items = TeamStandingsReadListAction.execute(db, user_id=current_user, team_id=payload.teamID, league_id=payload.leagueID)
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='team-standings',
            resource_id_key='teamStandingID',
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()
