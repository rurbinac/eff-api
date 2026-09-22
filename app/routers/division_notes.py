from fastapi import APIRouter, Form, Query

from app.actions.division_notes import DivisionNotesReadListAction
from app.context import RequestContext
from app.database import CurrentUser, DbSession
from app.exceptions import UnknownActionException
from app.guards import require_league_member
from app.utils import JsonApiSerializer

router = APIRouter(tags=["division-notes"])


@router.post("/eff/eff_api/DivisionNotes.php")
async def legacy_division_notes(
    db: DbSession,
    current_user: CurrentUser,
    f: str = Query(..., description="Action name"),
    type: str | None = Form(None, alias="_type"),
    divisionID: int = Form(...),
):
    """Legacy PHP-compatible endpoint for DivisionNotes actions."""
    RequestContext.set_datetime()

    try:
        if f == "ReadList":
            if type == "byDivisionID":
                require_league_member(db, current_user, division_id=divisionID)
                items = DivisionNotesReadListAction.execute(db, division_id=divisionID, user_id=current_user)
                return {
                    "table": "DivisionNotes",
                    "timestamp": RequestContext.get_datetime_iso(),
                    "items": [{"values": item} for item in items]
                }
            else:
                raise UnknownActionException(f, type)
        else:
            raise UnknownActionException(f)
    finally:
        RequestContext.reset()


@router.get("/api/v1/division_notes")
def rest_division_notes(db: DbSession, current_user: CurrentUser, divisionID: int | None = None):
    """REST endpoint: Get notes for division (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        items = DivisionNotesReadListAction.execute(db, division_id=divisionID, user_id=current_user)
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='division-notes',
            resource_id_key='divisionNoteID',
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()
