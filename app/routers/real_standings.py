from fastapi import APIRouter, Query, Form, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.context import RequestContext
from app.actions.real_standings import RealStandingsReadListAction

router = APIRouter()


@router.post("/eff/eff_api/RealStandings.php")
async def legacy_real_standings(
    f: str = Query(...),
    format: str = Form("json", alias="_format"),
    type: str = Form(None, alias="_type"),
    realCompetitionID: int = Form(...),
    realCompetitionMatchDay: int = Form(...),
    divisionID: int = Form(None),
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible RealStandings endpoint."""
    RequestContext.set_datetime()
    try:
        if f == "ReadList":
            if type == "byDivisionID":
                return RealStandingsReadListAction.execute(**filter_params)
            else:
                return RealStandingsReadListAction.execute(**filter_params)
        else:
            return {"error": f"Unknown function: {f}"}
    finally:
        RequestContext.reset()


@router.post("/api/real-standings/readlist")
async def rest_real_standings(
    realCompetitionID: int,
    realCompetitionMatchDay: int,
    divisionID: int = None,
    db: Session = Depends(get_db),
):
    """REST endpoint for RealStandings ReadList."""
    RequestContext.set_datetime()
    try:
        return RealStandingsReadListAction.execute(**filter_params)
    finally:
        RequestContext.reset()
