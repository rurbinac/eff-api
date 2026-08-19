from fastapi import APIRouter, Form, Query

from app.actions.teams import (
    TeamsGetCurrentMembersAction,
    TeamsGetRealMembersRankingAction,
    TeamsReadListAction,
    TeamsWaiverMembersDetailAction,
    TeamsWishListDetailAction,
)
from app.context import RequestContext
from app.database import DbSession
from app.utils import JsonApiSerializer

router = APIRouter(tags=["teams"])


@router.post("/eff/eff_api/Teams.php")
async def legacy_teams(
    db: DbSession,
    f: str = Query(..., description="Action name"),
    leagueID: int | None = Form(None),
    divisionID: int | None = Form(None),
    teamID: int | None = Form(None),
    type: str | None = Form(None, alias="_type"),
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
                "timestamp": RequestContext.get_datetime().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "items": [{"values": item} for item in items],
            }
        elif f == "GetCurrentMembers":
            if teamID is None:
                return {"error": "teamID is required for GetCurrentMembers"}, 400
            items = TeamsGetCurrentMembersAction.execute(db, teamID)
            return {
                "table": "RealTeamMembers",
                "timestamp": RequestContext.get_datetime().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "items": [{"values": item} for item in items],
            }
        elif f == "GetRealMembersRanking":
            if teamID is None:
                return {"error": "teamID is required for GetRealMembersRanking"}, 400
            items = TeamsGetRealMembersRankingAction.execute(db, teamID)
            return {
                "table": "RealTeamMembers",
                "timestamp": RequestContext.get_datetime().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "items": [{"values": item} for item in items],
            }
        elif f == "WaiverMembersDetail":
            if teamID is None:
                return {"error": "teamID is required for WaiverMembersDetail"}, 400
            items = TeamsWaiverMembersDetailAction.execute(db, teamID)
            return {
                "table": "WaiverMembers",
                "timestamp": RequestContext.get_datetime().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "items": [{"values": item} for item in items],
            }
        elif f == "WishListDetail":
            if teamID is None:
                return {"error": "teamID is required for WishListDetail"}, 400
            items = TeamsWishListDetailAction.execute(db, teamID)
            return {
                "table": "WishList",
                "timestamp": RequestContext.get_datetime().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "items": [{"values": item} for item in items],
            }
        else:
            return {"error": f"Unknown action: {f}"}, 400
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
