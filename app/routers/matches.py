from fastapi import APIRouter, Query, Form, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.context import RequestContext
from app.actions.matches import MatchesReadListAction

router = APIRouter()


@router.post("/eff/eff_api/Matches.php")
async def legacy_matches(
    f: str = Query(...),
    format: str = Form("json", alias="_format"),
    type: str = Form(None, alias="_type"),
    leagueID: int = Form(None),
    divisionID: int = Form(None),
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible Matches endpoint."""
    RequestContext.set_datetime()
    try:
        if f == "ReadList":
            if type == "byDivisionID":
                return MatchesReadListAction.execute(**filter_params)
            else:
                return MatchesReadListAction.execute(**filter_params)
        else:
            return {"error": f"Unknown function: {f}"}
    finally:
        RequestContext.reset()


@router.post("/api/matches/readlist")
async def rest_matches(
    leagueID: int = None,
    divisionID: int = None,
    db: Session = Depends(get_db),
):
    """REST endpoint for Matches ReadList."""
    RequestContext.set_datetime()
    try:
        return MatchesReadListAction.execute(**filter_params)
    finally:
        RequestContext.reset()
