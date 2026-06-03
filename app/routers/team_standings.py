from fastapi import APIRouter, Query, Form, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.context import RequestContext
from app.actions.team_standings import TeamStandingsReadListAction

router = APIRouter()


@router.post("/eff/eff_api/TeamStandings.php")
async def legacy_team_standings(
    f: str = Query(...),
    format: str = Form("json", alias="_format"),
    type: str = Form(None, alias="_type"),
    leagueID: int = Form(None),
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible TeamStandings endpoint."""
    RequestContext.set_datetime()
    try:
        if f == "ReadList":
            if type == "byLeagueID" and leagueID is not None:
                return TeamStandingsReadListAction.execute(db, league_id=leagueID)
            else:
                return TeamStandingsReadListAction.execute(db)
        else:
            return {"error": f"Unknown function: {f}"}
    finally:
        RequestContext.reset()


@router.post("/api/team-standings/readlist")
async def rest_team_standings(
    leagueID: int = None,
    db: Session = Depends(get_db),
):
    """REST endpoint for TeamStandings ReadList."""
    RequestContext.set_datetime()
    try:
        return TeamStandingsReadListAction.execute(db, league_id=leagueID)
    finally:
        RequestContext.reset()
