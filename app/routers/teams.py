from fastapi import APIRouter, Depends, Request, Query, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.actions.teams import TeamsReadListAction, TeamsGetRealMembersRankingAction, TeamsWaiverMembersDetailAction
from app.context import RequestContext


class TeamsRequest(BaseModel):
    leagueID: int | None = None
    divisionID: int | None = None
    teamID: int | None = None


router = APIRouter(tags=["teams"])


@router.post("/eff/eff_api/Teams.php")
async def legacy_teams(
    f: str = Query(..., description="Action name"),
    format: str | None = Query("json", alias="_format"),
    type: str | None = Query(None, alias="_type"),
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


@router.post("/api/teams/readlist")
def rest_teams(
    payload: TeamsRequest,
    db: Session = Depends(get_db)
):
    """REST endpoint: Get teams for league or division."""
    RequestContext.set_datetime()
    try:
        items = TeamsReadListAction.execute(db, league_id=payload.leagueID, division_id=payload.divisionID)
        return items
    finally:
        RequestContext.reset()


@router.post("/api/teams/real-members-ranking")
def rest_teams_real_members_ranking(
    payload: TeamsRequest,
    db: Session = Depends(get_db)
):
    """REST endpoint: Get real members ranking for team."""
    RequestContext.set_datetime()
    try:
        if payload.teamID is None:
            return {"error": "teamID is required"}, 400
        items = TeamsGetRealMembersRankingAction.execute(db, payload.teamID)
        return items
    finally:
        RequestContext.reset()


@router.post("/api/teams/waiver-members-detail")
def rest_teams_waiver_members_detail(
    payload: TeamsRequest,
    db: Session = Depends(get_db)
):
    """REST endpoint: Get waiver members detail for team."""
    RequestContext.set_datetime()
    try:
        if payload.teamID is None:
            return {"error": "teamID is required"}, 400
        items = TeamsWaiverMembersDetailAction.execute(db, payload.teamID)
        return items
    finally:
        RequestContext.reset()
