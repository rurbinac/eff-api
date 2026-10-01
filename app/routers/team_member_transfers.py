from fastapi import APIRouter, Form, Query
from pydantic import BaseModel

from app.actions.team_member_transfers import (
    TeamMemberTransfersAcceptAction,
    TeamMemberTransfersGetPendingByTeamIDAction,
    TeamMemberTransfersRejectAction,
    TeamMemberTransfersRequestAction,
    TeamMemberTransfersWithdrawAction,
)
from app.context import RequestContext
from app.database import CurrentUser, DbSession
from app.exceptions import EFFException, UnknownActionException
from app.guards import require_authentication, require_keys, require_pos_int
from app.utils import JsonApiSerializer
from app.utils.legacy_returns import return_error, return_many_legacy, return_one_legacy


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
    otherTeamID: int | None = Form(None),
    teamMemberTransferID: int | None = Form(None),
    requested: str | None = Form(None),
    offered: str | None = Form(None),
    addDrop: str | None = Form(None),
):
    """Legacy PHP-compatible endpoint for TeamMemberTransfers actions."""
    RequestContext.set_datetime()

    try:

        require_authentication(current_user)

        if f == "Request":
            require_pos_int(teamID, "teamID", f)
            require_pos_int(otherTeamID, "otherTeamID", f)
            req_keys = require_keys(requested, f)
            off_keys = require_keys(offered, f)
            drop_keys = require_keys(addDrop, f)
            values = TeamMemberTransfersRequestAction.execute(
                db, user_id=current_user, team_id=teamID, other_team_id=otherTeamID,
                requested=req_keys, offered=off_keys, add_drop=drop_keys,
            )
            return return_one_legacy("TeamMemberTransfers", values)

        elif f == "GetPendingByTeamID":
            if type == "byLeagueID":
                require_pos_int(teamID, "teamID", f)
                items = TeamMemberTransfersGetPendingByTeamIDAction.execute(db, current_user, teamID)
                return return_many_legacy("TeamMemberTransfers", items)
            else:
                raise UnknownActionException(f, type)

        elif f == "Accept":
            require_pos_int(teamMemberTransferID, "teamMemberTransferID", f)
            keys = require_keys(addDrop, f)
            values = TeamMemberTransfersAcceptAction.execute(
                db, transfer_id=teamMemberTransferID, user_id=current_user, add_drop=keys,
            )
            return return_one_legacy("TeamMemberTransfers", values)

        elif f == "Reject":
            require_pos_int(teamMemberTransferID, "teamMemberTransferID", f)
            values = TeamMemberTransfersRejectAction.execute(
                db, transfer_id=teamMemberTransferID, user_id=current_user,
            )
            return return_one_legacy("TeamMemberTransfers", values)

        elif f == "Withdraw":
            require_pos_int(teamMemberTransferID, "teamMemberTransferID", f)
            values = TeamMemberTransfersWithdrawAction.execute(
                db, transfer_id=teamMemberTransferID, user_id=current_user,
            )
            return return_one_legacy("TeamMemberTransfers", values)

        else:
            raise UnknownActionException(f)

    except EFFException as e:
        return return_error(e)
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
        items = TeamMemberTransfersGetPendingByTeamIDAction.execute(db, current_user, payload.teamID)
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='team-member-transfers',
            resource_id_key='teamMemberTransferID',
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()
