from fastapi import APIRouter, Query, Form, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.context import RequestContext
from app.actions.real_matches import RealMatchesReadListAction

router = APIRouter()


@router.post("/eff/eff_api/RealMatches.php")
async def legacy_real_matches(
    f: str = Query(...),
    format: str = Form("json", alias="_format"),
    type: str = Form(None, alias="_type"),
    realCompetitionID: int = Form(None),
    realCompetitionMatchDay: int = Form(None),
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible RealMatches endpoint."""
    RequestContext.set_datetime()
    try:
        if f == "ReadList":
            if type == "byMatchDay":
                return RealMatchesReadListAction.execute(**filter_params)
            else:
                return RealMatchesReadListAction.execute(**filter_params)
        else:
            return {"error": f"Unknown function: {f}"}
    finally:
        RequestContext.reset()


@router.post("/api/real-matches/readlist")
async def rest_real_matches(
    realCompetitionID: int = None,
    realCompetitionMatchDay: int = None,
    db: Session = Depends(get_db),
):
    """REST endpoint for RealMatches ReadList."""
    RequestContext.set_datetime()
    try:
        return RealMatchesReadListAction.execute(**filter_params)
    finally:
        RequestContext.reset()
