from fastapi import APIRouter, Query, Form, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.context import RequestContext
from app.actions.match_teams import MatchTeamsReadListAction

router = APIRouter()


@router.post("/eff/eff_api/MatchTeams.php")
async def legacy_match_teams(
    f: str = Query(...),
    format: str = Form("json", alias="_format"),
    type: str = Form(None, alias="_type"),
    teamID: int = Form(None),
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible MatchTeams endpoint."""
    RequestContext.set_datetime()
    try:
        if f == "ReadList":
            if type == "byTeamID":
                return MatchTeamsReadListAction.execute(db, team_id=teamID)
            else:
                return MatchTeamsReadListAction.execute(db)
        else:
            return {"error": f"Unknown function: {f}"}
    finally:
        RequestContext.reset()


@router.post("/api/match-teams/readlist")
async def rest_match_teams(
    teamID: int = None,
    db: Session = Depends(get_db),
):
    """REST endpoint for MatchTeams ReadList."""
    RequestContext.set_datetime()
    try:
        return MatchTeamsReadListAction.execute(db, team_id=teamID)
    finally:
        RequestContext.reset()
