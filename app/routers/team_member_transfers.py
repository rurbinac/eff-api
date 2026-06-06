from fastapi import APIRouter, Depends, Query, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.actions.team_member_transfers import TeamMemberTransfersGetPendingByTeamIDAction
from app.context import RequestContext


class TeamMemberTransfersRequest(BaseModel):
    teamID: int | None = None


router = APIRouter(tags=["team-member-transfers"])


@router.post("/eff/eff_api/TeamMemberTransfers.php")
async def legacy_team_member_transfers(
    f: str = Query(..., description="Action name"),
    format: str | None = Query("json", alias="_format"),
    teamID: int | None = Form(None),
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible endpoint for TeamMemberTransfers actions."""
    RequestContext.set_datetime()

    try:
        if f == "GetPendingByTeamID":
            if teamID is None:
                return {"error": "teamID is required for GetPendingByTeamID"}, 400
            items = TeamMemberTransfersGetPendingByTeamIDAction.execute(db, teamID)
            return {
                "table": "TeamMemberTransfers",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items]
            }
        else:
            return {"error": f"Unknown action: {f}"}, 400
    finally:
        RequestContext.reset()


@router.post("/api/team-member-transfers/pending")
def rest_team_member_transfers_pending(
    payload: TeamMemberTransfersRequest,
    db: Session = Depends(get_db)
):
    """REST endpoint: Get pending member transfers for team."""
    RequestContext.set_datetime()
    try:
        if payload.teamID is None:
            return {"error": "teamID is required"}, 400
        items = TeamMemberTransfersGetPendingByTeamIDAction.execute(db, payload.teamID)
        return items
    finally:
        RequestContext.reset()
