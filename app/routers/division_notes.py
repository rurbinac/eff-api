from fastapi import APIRouter, Form, Query

from app.actions.division_notes import DivisionNotesReadListAction
from app.context import RequestContext
from app.database import DbSession
from app.utils import JsonApiSerializer

router = APIRouter(tags=["division-notes"])


@router.post("/eff/eff_api/DivisionNotes.php")
async def legacy_division_notes(
    db: DbSession,
    f: str = Query(..., description="Action name"),
    divisionID: int = Form(...),
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


@router.get("/api/v1/division_notes")
def rest_division_notes(db: DbSession, divisionID: int | None = None):
    """REST endpoint: Get notes for division (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        items = DivisionNotesReadListAction.execute(db, division_id=divisionID)
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='division-notes',
            resource_id_key='divisionNoteID',
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()
