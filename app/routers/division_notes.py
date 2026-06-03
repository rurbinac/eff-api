from fastapi import APIRouter, Depends, Request, Query, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.actions.division_notes import DivisionNotesReadListAction
from app.context import RequestContext

router = APIRouter(tags=["division-notes"])


@router.post("/eff/eff_api/DivisionNotes.php")
async def legacy_division_notes(
    f: str = Query(..., description="Action name"),
    _format: str | None = Query("json"),
    _type: str | None = Query(None),
    divisionID: int = Form(...),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible endpoint for DivisionNotes actions."""
    RequestContext.set_datetime()

    try:
        if f == "ReadList":
            result = DivisionNotesReadListAction.execute(db, divisionID)
            return result
        else:
            return {"error": f"Unknown action: {f}"}, 400
    finally:
        RequestContext.reset()


@router.post("/api/division-notes/readlist")
def rest_division_notes(divisionID: int, db: Session = Depends(get_db)):
    """REST endpoint: Get notes for division."""
    RequestContext.set_datetime()
    try:
        result = DivisionNotesReadListAction.execute(db, divisionID)
        # For REST API, return simplified format (no items wrapper)
        return {
            "notes": [item["values"] for item in result["items"]],
            "timestamp": result["timestamp"],
        }
    finally:
        RequestContext.reset()
