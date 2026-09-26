from fastapi import APIRouter, Form, Query

from app.actions.division_notes import (
    DivisionNotesCreateAction,
    DivisionNotesDeleteAction,
    DivisionNotesReadListAction,
    DivisionNotesUpdateAction,
)
from app.context import RequestContext
from app.database import CurrentUser, DbSession
from app.exceptions import EFFException, UnknownActionException
from app.guards import (
    require_authentication,
    require_pos_int,
)
from app.utils.legacy_returns import return_error, return_many_legacy, return_one_legacy

router = APIRouter(tags=["division-notes"])


@router.post("/eff/eff_api/DivisionNotes.php")
async def legacy_division_notes(
    db: DbSession,
    current_user: CurrentUser,
    f: str = Query(..., description="Action name"),
    type: str | None = Form(None, alias="_type"),
    divisionID: int | None = Form(None),
    teamID: int | None = Form(None),
    parentDivisionNoteID: int | None = Form(None),
    title: str | None = Form(None),
    notes: str | None = Form(None),
    divisionNoteType: str | None = Form(None),
    divisionNoteID: int | None = Form(None),
):
    """Legacy PHP-compatible endpoint for DivisionNotes actions."""
    RequestContext.set_datetime()

    try:
        require_authentication(current_user)

        if f == "ReadList":
            if type == "byDivisionID":
                require_pos_int(divisionID, "divisionID", f"{f}({type})")
                items = DivisionNotesReadListAction.execute(db, division_id=divisionID, user_id=current_user)
            else:
                raise UnknownActionException(f, type)
            return return_many_legacy("DivisionNotes", items)

        elif f == "Create":
            require_pos_int(teamID, "teamID", f)
            item = DivisionNotesCreateAction.execute(
                db,
                user_id=current_user,
                team_id=teamID,
                title=title,
                division_note_type=divisionNoteType,
                notes=notes,
                parent_division_note_id=parentDivisionNoteID,
            )
            return return_one_legacy("DivisionNotes", item)

        elif f == "Update":
            require_pos_int(divisionNoteID, "divisionNoteID", f)
            item = DivisionNotesUpdateAction.execute(
                db,
                user_id=current_user,
                division_note_id=divisionNoteID,
                title=title,
                notes=notes,
            )
            return return_one_legacy("DivisionNotes", item)

        elif f == "Delete":
            require_pos_int(divisionNoteID, "divisionNoteID", f)
            item = DivisionNotesDeleteAction.execute(
                db,
                user_id=current_user,
                division_note_id=divisionNoteID,
            )
            return return_one_legacy("DivisionNotes", item)

        else:
            raise UnknownActionException(f)
    except EFFException as e:
        return return_error(e)
    finally:
        RequestContext.reset()
