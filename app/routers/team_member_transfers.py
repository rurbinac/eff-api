from fastapi import APIRouter, Form, Query
from pydantic import BaseModel

from app.actions.team_member_transfers import (
    TeamMemberTransfersGetPendingByTeamIDAction,
)
from app.context import RequestContext
from app.database import CurrentUser, DbSession
from app.exceptions import UnknownActionException
from app.guards import require_pos_int
from app.utils import JsonApiSerializer


class TeamMemberTransfersRequest(BaseModel):
    teamID: int | None = None


router = APIRouter(tags=["team-member-transfers"])


@router.post("/eff/eff_api/TeamMemberTransfers.php")
async def legacy_team_member_transfers(
    db: DbSession,
    current_user: CurrentUser,
    f: str = Query(..., description="Action name"),
    type: str | None = Form(None, alias="_type"),
    teamID: int | None = Form(None),
):
    """Legacy PHP-compatible endpoint for TeamMemberTransfers actions."""
    RequestContext.set_datetime()

    try:
        if f == "GetPendingByTeamID":
            if type == "byLeagueID":
                require_pos_int(teamID, "teamID", f)
                items = TeamMemberTransfersGetPendingByTeamIDAction.execute(db, teamID, current_user)
                return {
                    "table": "TeamMemberTransfers",
                    "timestamp": RequestContext.get_datetime_iso(),
                    "items": [{"values": item} for item in items]
                }
            else:
                raise UnknownActionException(f, type)
        else:
            raise UnknownActionException(f)
    finally:
        RequestContext.reset()


@router.get("/api/v1/team-member-transfers/pending")
def rest_team_member_transfers_pending(
    payload: TeamMemberTransfersRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    """REST endpoint: Get pending member transfers for team (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        if payload.teamID is None:
            return JsonApiSerializer.serialize_error(400, "Bad Request", "teamID is required")
        items = TeamMemberTransfersGetPendingByTeamIDAction.execute(db, payload.teamID, current_user)
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='team-member-transfers',
            resource_id_key='teamMemberTransferID',
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()
