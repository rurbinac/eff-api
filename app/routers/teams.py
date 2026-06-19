from fastapi import APIRouter, Depends, Request, Query, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.actions.teams import TeamsReadListAction, TeamsGetRealMembersRankingAction, TeamsWaiverMembersDetailAction, TeamsGetCurrentMembersAction
from app.context import RequestContext
from app.utils import JsonApiSerializer


class TeamsRequest(BaseModel):
    leagueID: int | None = None
    divisionID: int | None = None
    teamID: int | None = None


router = APIRouter(tags=["teams"])


@router.post("/eff/eff_api/Teams.php")
async def legacy_teams(
    f: str = Query(..., description="Action name"),
    format: str | None = Query("json", alias="_format"),
    type: str | None = Form(None, alias="_type"),
    leagueID: int | None = Form(None),
    divisionID: int | None = Form(None),
    teamID: int | None = Form(None),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible endpoint for Teams actions."""
    RequestContext.set_datetime()

    try:
        if f == "ReadList":
            if type == "byDivisionID":
                items = TeamsReadListAction.execute(db, division_id=divisionID)
            else:
                items = TeamsReadListAction.execute(db, league_id=leagueID)
            return {
                "table": "Teams",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items]
            }
        elif f == "GetRealMembersRanking":
            if teamID is None:
                return {"error": "teamID is required for GetRealMembersRanking"}, 400
            items = TeamsGetRealMembersRankingAction.execute(db, teamID)
            return {
                "table": "RealTeamMembers",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items]
            }
        elif f == "WaiverMembersDetail":
            if teamID is None:
                return {"error": "teamID is required for WaiverMembersDetail"}, 400
            items = TeamsWaiverMembersDetailAction.execute(db, teamID)
            return {
                "table": "WaiverMembers",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items]
            }
        else:
            return {"error": f"Unknown action: {f}"}, 400
    finally:
        RequestContext.reset()


@router.get("/api/v1/teams")
def rest_teams(
    leagueID: int | None = None,
    divisionID: int | None = None,
    db: Session = Depends(get_db)
):
    """REST endpoint: Get teams for league or division (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        items = TeamsReadListAction.execute(db, league_id=leagueID, division_id=divisionID)
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='teams',
            resource_id_key='teamID',
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()


@router.get("/api/v1/teams/waiver_members_detail")
def rest_teams_waiver_members_detail(
    teamID: int | None = None,
    db: Session = Depends(get_db)
):
    """REST endpoint: Get waiver members detail for team (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        if teamID is None:
            return JsonApiSerializer.serialize_error(400, "Bad Request", "teamID is required")
        items = TeamsWaiverMembersDetailAction.execute(db, teamID)
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='waiver-members',
            resource_id_key='teamMemberID',
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()


@router.get("/api/v1/teams/wish_list_detail")
def rest_teams_wish_list_detail(
    teamID: int | None = None,
    db: Session = Depends(get_db)
):
    """REST endpoint: Get wish list detail for team (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        if teamID is None:
            return JsonApiSerializer.serialize_error(400, "Bad Request", "teamID is required")
        # TODO: Implement TeamsWishListDetailAction
        items = []
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='wish-list',
            resource_id_key='teamID',
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()


@router.get("/api/v1/teams/current_members")
def rest_teams_current_members(
    teamID: int | None = None,
    db: Session = Depends(get_db)
):
    """REST endpoint: Get current members for team (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        if teamID is None:
            return JsonApiSerializer.serialize_error(400, "Bad Request", "teamID is required")
        items = TeamsGetCurrentMembersAction.execute(db, teamID)
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='team-members',
            resource_id_key='realTeamMemberKey',
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()


@router.get("/api/v1/teams/real_members_ranking")
def rest_teams_real_members_ranking(
    teamID: int | None = None,
    db: Session = Depends(get_db)
):
    """REST endpoint: Get real members ranking for team (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        if teamID is None:
            return JsonApiSerializer.serialize_error(400, "Bad Request", "teamID is required")
        items = TeamsGetRealMembersRankingAction.execute(db, teamID)
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='team-members',
            resource_id_key='realTeamMemberID',
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()
