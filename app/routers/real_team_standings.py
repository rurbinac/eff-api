from fastapi import APIRouter, Query, Form, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.context import RequestContext
from app.actions.real_team_standings import RealTeamStandingsReadListAction

router = APIRouter()


@router.post("/eff/eff_api/RealTeamStandings.php")
async def legacy_real_team_standings(
    f: str = Query(...),
    format: str = Form("json", alias="_format"),
    type: str = Form(None, alias="_type"),
    realCompetitionID: int = Form(...),
    realCompetitionMatchDay: int = Form(...),
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible RealTeamStandings endpoint."""
    RequestContext.set_datetime()
    try:
        if f == "ReadList":
            return RealTeamStandingsReadListAction.execute(**filter_params)
        else:
            return {"error": f"Unknown function: {f}"}
    finally:
        RequestContext.reset()


@router.post("/api/real-team-standings/readlist")
async def rest_real_team_standings(
    realCompetitionID: int,
    realCompetitionMatchDay: int,
    db: Session = Depends(get_db),
):
    """REST endpoint for RealTeamStandings ReadList."""
    RequestContext.set_datetime()
    try:
        return RealTeamStandingsReadListAction.execute(**filter_params)
    finally:
        RequestContext.reset()
