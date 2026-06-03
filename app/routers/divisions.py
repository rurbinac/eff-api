from fastapi import APIRouter, Depends, Request, Query, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.actions.divisions import DivisionsReadListAction
from app.context import RequestContext

router = APIRouter(tags=["divisions"])


@router.post("/eff/eff_api/Divisions.php")
async def legacy_divisions(
    f: str = Query(..., description="Action name"),
    format: str | None = Query("json", alias="_format"),
    type: str | None = Query(None, alias="_type"),
    leagueID: int = Form(...),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible endpoint for Divisions actions."""
    RequestContext.set_datetime()

    try:
        if f == "ReadList":
            result = DivisionsReadListAction.execute(db, leagueID)
            return result
        else:
            return {"error": f"Unknown action: {f}"}, 400
    finally:
        RequestContext.reset()


@router.post("/api/divisions/readlist")
def rest_divisions(leagueID: int, db: Session = Depends(get_db)):
    """REST endpoint: Get divisions for league."""
    RequestContext.set_datetime()
    try:
        result = DivisionsReadListAction.execute(db, leagueID)
        # For REST API, return simplified format (no items wrapper)
        return {
            "divisions": [item["values"] for item in result["items"]],
            "timestamp": result["timestamp"],
        }
    finally:
        RequestContext.reset()
