from fastapi import APIRouter, Depends, Request, Query, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.actions.division_notes import DivisionNotesReadListAction
from app.context import RequestContext

router = APIRouter(tags=["division-notes"])


@router.post("/eff/eff_api/DivisionNotes.php")
async def legacy_division_notes(
    f: str = Query(..., description="Action name"),
    format: str | None = Query("json", alias="_format"),
    type: str | None = Query(None, alias="_type"),
    divisionID: int = Form(...),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible endpoint for DivisionNotes actions."""
    RequestContext.set_datetime()

    try:
        if f == "ReadList":
            items = DivisionNotesReadListAction.execute(db, division_id=divisionID)
            return {
                "table": "DivisionNotes",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items]
            }
        else:
            return {"error": f"Unknown action: {f}"}, 400
    finally:
        RequestContext.reset()


@router.post("/api/divisionnotes/readlist")
def rest_division_notes(divisionID: int, db: Session = Depends(get_db)):
    """REST endpoint: Get notes for division."""
    RequestContext.set_datetime()
    try:
        result = DivisionNotesReadListAction.execute(db, division_id=divisionID)
        return result
    finally:
        RequestContext.reset()
