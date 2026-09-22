from fastapi import APIRouter, Form, Query
from pydantic import BaseModel

from app.actions.teams import (
    TeamsGetCurrentMembersAction,
    TeamsGetRealMembersRankingAction,
    TeamsReadListAction,
    TeamsUpdateAction,
    TeamsWaiverMembersDetailAction,
    TeamsWishListDetailAction,
)
from app.context import RequestContext
from app.database import CurrentUser, DbSession
from app.exceptions import EFFException, UnknownActionException
from app.guards import (
    require_authentication,
    require_league_member,
    require_pos_int,
    require_team_owner,
)
from app.utils import JsonApiSerializer
from app.utils.returns import return_error, return_many_legacy, return_one_legacy

router = APIRouter(tags=["teams"])


@router.post("/eff/eff_api/Teams.php")
async def legacy_teams(
    db: DbSession,
    current_user: CurrentUser,
    f: str = Query(..., description="Action name"),
    leagueID: int | None = Form(None),
    divisionID: int | None = Form(None),
    teamID: int | None = Form(None),
    teamName: str | None = Form(None),
    notes: str | None = Form(None),
    type: str | None = Form(None, alias="_type"),
):
    """Legacy PHP-compatible endpoint for Teams actions."""
    RequestContext.set_datetime()

    try:
        require_authentication(current_user)
        if f == "ReadList":
            if type == "byLeagueID":
                require_pos_int(leagueID, "leagueID", f"{f}({type})")
                require_league_member(db, current_user, league_id=leagueID)
                items = TeamsReadListAction.execute(db, league_id=leagueID)
            elif type == "byDivisionID":
                require_pos_int(divisionID, "divisionID", f"{f}({type})")
                require_league_member(db, current_user, division_id=divisionID)
                items = TeamsReadListAction.execute(db, division_id=divisionID)
            else:
                raise UnknownActionException(f, type)
            return return_many_legacy("Teams", items)
        elif f == "GetCurrentMembers":
            require_pos_int(teamID, "teamID", f)
            require_league_member(db, current_user, team_id=teamID)
            items = TeamsGetCurrentMembersAction.execute(db, teamID)
            return return_many_legacy("RealTeamMembers", items)
        elif f == "GetRealMembersRanking":
            require_pos_int(teamID, "teamID", f)
            require_league_member(db, current_user, team_id=teamID)
            items = TeamsGetRealMembersRankingAction.execute(db, teamID)
            return return_many_legacy("RealTeamMembers", items)
        elif f == "WaiverMembersDetail":
            require_pos_int(teamID, "teamID", f)
            require_league_member(db, current_user, team_id=teamID)
            items = TeamsWaiverMembersDetailAction.execute(db, teamID)
            return return_many_legacy("WaiverMembers", items)
        elif f == "WishListDetail":
            require_pos_int(teamID, "teamID", f)
            require_league_member(db, current_user, team_id=teamID)
            items = TeamsWishListDetailAction.execute(db, teamID)
            return return_many_legacy("WishList", items)
        elif f == "Update":
            require_pos_int(teamID, "teamID", f)
            require_team_owner(db, current_user, teamID)
            values = TeamsUpdateAction.execute(
                db,
                team_id=teamID,
                user_id=current_user,
                team_name=teamName,
                notes=notes,
            )
            return return_one_legacy("Teams", values)
        else:
            raise UnknownActionException(f)
    except EFFException as e:
        return return_error(e)
    finally:
        RequestContext.reset()


@router.get("/api/v1/teams")
def rest_teams(
    db: DbSession,
    leagueID: int | None = None,
    divisionID: int | None = None,
):
    """REST endpoint: Get teams for league or division (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        items = TeamsReadListAction.execute(
            db, league_id=leagueID, division_id=divisionID
        )
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type="teams",
            resource_id_key="teamID",
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()


@router.get("/api/v1/teams/waiver_members_detail")
def rest_teams_waiver_members_detail(
    db: DbSession,
    teamID: int | None = None,
):
    """REST endpoint: Get waiver members detail for team (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        if teamID is None:
            return JsonApiSerializer.serialize_error(
                400, "Bad Request", "teamID is required"
            )
        items = TeamsWaiverMembersDetailAction.execute(db, teamID)
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type="waiver-members",
            resource_id_key="teamMemberID",
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()


@router.get("/api/v1/teams/wish_list_detail")
def rest_teams_wish_list_detail(
    db: DbSession,
    teamID: int | None = None,
):
    """REST endpoint: Get wish list detail for team (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        if teamID is None:
            return JsonApiSerializer.serialize_error(
                400, "Bad Request", "teamID is required"
            )
        items = TeamsWishListDetailAction.execute(db, teamID)
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type="wish-list",
            resource_id_key="realTeamMemberKey",
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()


@router.get("/api/v1/teams/current_members")
def rest_teams_current_members(
    db: DbSession,
    teamID: int | None = None,
):
    """REST endpoint: Get current members for team (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        if teamID is None:
            return JsonApiSerializer.serialize_error(
                400, "Bad Request", "teamID is required"
            )
        items = TeamsGetCurrentMembersAction.execute(db, teamID)
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type="team-members",
            resource_id_key="realTeamMemberKey",
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()


@router.get("/api/v1/teams/real_members_ranking")
def rest_teams_real_members_ranking(
    db: DbSession,
    teamID: int | None = None,
):
    """REST endpoint: Get real members ranking for team (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        if teamID is None:
            return JsonApiSerializer.serialize_error(
                400, "Bad Request", "teamID is required"
            )
        items = TeamsGetRealMembersRankingAction.execute(db, teamID)
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type="team-members",
            resource_id_key="realTeamMemberID",
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()


class TeamsUpdateRequest(BaseModel):
    teamName: str | None = None
    notes: str | None = None


@router.patch("/api/v1/teams/{team_id}")
async def rest_teams_update(
    team_id: int,
    payload: TeamsUpdateRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    """Update editable team settings (team owner only)."""
    RequestContext.set_datetime()
    try:
        require_authentication(current_user)
        values = TeamsUpdateAction.execute(
            db,
            team_id=team_id,
            user_id=current_user,
            team_name=payload.teamName,
            notes=payload.notes,
        )
        return {
            "data": {
                "type": "teams",
                "id": str(team_id),
                "attributes": values,
            },
            "meta": {"timestamp": RequestContext.get_datetime_iso()},
        }
    finally:
        RequestContext.reset()
