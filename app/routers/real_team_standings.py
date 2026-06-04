from fastapi import APIRouter, Query, Form, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.context import RequestContext
from app.actions.real_team_standings import RealTeamStandingsReadListAction

router = APIRouter(tags=["real-team-standings"])


@router.post("/eff/eff_api/RealTeamStandings.php")
async def legacy_real_team_standings(
    f: str = Query(...),
    format: str | None = Query("json", alias="_format"),
    type: str | None = Query(None, alias="_type"),
    realCompetitionID: int | None = Form(None),
    realCompetitionSeasonID: int | None = Form(None),
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible RealTeamStandings endpoint."""
    RequestContext.set_datetime()
    try:
        if f == "ReadList":
            items = RealTeamStandingsReadListAction.execute(
                db,
                real_competition_id=realCompetitionID,
                real_competition_season_id=realCompetitionSeasonID
            )
            return {
                "table": "RealTeamStandings",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items]
            }
        else:
            return {"error": f"Unknown function: {f}"}, 400
    finally:
        RequestContext.reset()


@router.post("/api/realteamstandings/readlist")
async def rest_real_team_standings(
    realCompetitionID: int,
    realCompetitionSeasonID: int,
    db: Session = Depends(get_db),
):
    """REST endpoint for RealTeamStandings ReadList."""
    RequestContext.set_datetime()
    try:
        items = RealTeamStandingsReadListAction.execute(
            db,
            real_competition_id=realCompetitionID,
            real_competition_season_id=realCompetitionSeasonID
        )
        return items
    finally:
        RequestContext.reset()
