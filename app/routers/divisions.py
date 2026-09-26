import json
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.actions.divisions import (
    DivisionsReadListAction,
    DivisionsTransactionsDetailAction,
    DivisionsUpdateAction,
)
from app.actions.draft import DraftResultAction, DraftSituationAction
from app.actions.draft.draft_exception import DraftException
from app.actions.draft.draft_helper import DraftHelper
from app.actions.draft.draft_values import DraftValues
from app.context import RequestContext
from app.database import CurrentUser, DbSession
from app.exceptions import EFFException, NotFoundException, UnknownActionException
from app.guards import (
    require_authentication,
    require_division_commissioner,
    require_league_member,
    require_pos_int,
)
from app.models import Division
from app.services import pusher as pusher_service
from app.utils import JsonApiSerializer
from app.utils.legacy_returns import return_error, return_many_legacy, return_one_legacy

router = APIRouter(tags=["divisions"])


def _auth_helper(
    db: Session, user_id: int | None, division_id: int
) -> tuple[DraftHelper, HTTPException | None]:
    if user_id is None:
        return None, HTTPException(status_code=401, detail="Missing or invalid token")
    dh = DraftHelper(db, user_id, division_id)
    dh.draft_values.load_division()
    if dh.draft_values.division is None:
        return None, HTTPException(status_code=404, detail="Division not found")
    return dh, None


def _draft_response(division_id: int, dv: DraftValues) -> dict:
    d = dv.division
    return {
        "data": {
            "type": "divisions",
            "id": str(division_id),
            "attributes": {
                "draftStatus": d.get("draftStatus"),
                "draftingStart": d.get("draftingStart"),
                "draftingLimit": d.get("draftingLimit"),
            },
        },
        "meta": {
            "timestamp": RequestContext.get_datetime_iso()
        },
    }


@router.post("/eff/eff_api/Divisions.php")
async def legacy_divisions(
    db: DbSession,
    current_user: CurrentUser,
    f: str = Query(..., description="Action name"),
    type: str | None = Form(None, alias="_type"),
    leagueID: int | None = Form(None),
    divisionID: int | None = Form(None),
    draftType: str | None = Form(None),
    draftDate: Annotated[datetime | None, Form()] = None,
    draftCompleteDate: Annotated[datetime | None, Form()] = None,
):
    """Legacy PHP-compatible endpoint for Divisions actions."""
    RequestContext.set_datetime()

    try:
        require_authentication(current_user)
        if f == "ReadList":
            if type == "byLeagueID":
                require_pos_int(leagueID, "leagueID", f"{f}({type})")
                require_league_member(db, current_user, league_id=leagueID)
                items = DivisionsReadListAction.execute(db, leagueID)
            else:
                raise UnknownActionException(f, type)
            return return_many_legacy("Divisions", items)
        elif f == "Update":
            require_pos_int(divisionID, "divisionID", f)
            values = DivisionsUpdateAction.execute(
                db,
                division_id=divisionID,
                user_id=current_user,
                draft_type=draftType,
                draft_date=draftDate,
                draft_complete_date=draftCompleteDate,
            )
            return return_one_legacy("Divisions", values)
        elif f == "TransactionsDetail":
            require_pos_int(divisionID, "divisionID", f)
            items = DivisionsTransactionsDetailAction.execute(db, divisionID, current_user)
            return return_many_legacy("TransactionsDetail", items)
        elif f == "DraftResult":
            require_pos_int(divisionID, "divisionID", f)
            items = DraftResultAction.execute(db, divisionID, user_id=current_user)
            return return_many_legacy("DraftResult", items)
        elif f == "DraftSituation":
            require_pos_int(divisionID, "divisionID", f)
            require_league_member(db, current_user, division_id=divisionID)
            result = DraftSituationAction.execute(db, divisionID)
            if result is None:
                raise NotFoundException("Division", divisionID)
            return return_one_legacy("DraftSituation", result)
        elif f in ("StartDraft", "PauseDraft", "RestartDraft"):
            require_pos_int(divisionID, "divisionID", f)
            require_division_commissioner(db, current_user, division_id=divisionID)
            dh, auth_err = _auth_helper(db, current_user, divisionID)
            if auth_err:
                raise auth_err
            try:
                action = {
                    "StartDraft": dh.start,
                    "PauseDraft": dh.pause,
                    "RestartDraft": dh.restart,
                }[f]
                action()
            except DraftException as e:
                return PlainTextResponse(e.legacy_response(), status_code=e.status_code)
            dv = dh.draft_values
            return return_one_legacy(f, {
                "divisionID": divisionID,
                "draftStatus": dv.division.get("draftStatus"),
                "draftingStart": dv.division.get("draftingStart"),
                "draftingLimit": dv.division.get("draftingLimit"),
            })
        else:
            raise UnknownActionException(f)
    except EFFException as e:
        return return_error(e)
    finally:
        RequestContext.reset()


@router.get("/api/v1/divisions")
def rest_divisions(db: DbSession, leagueID: int | None = None):
    """REST endpoint: Get divisions for league (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        if leagueID is None:
            return JsonApiSerializer.serialize_error(
                400, "Bad Request", "leagueID is required"
            )
        items = DivisionsReadListAction.execute(db, leagueID)
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type="divisions",
            resource_id_key="divisionID",
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()


@router.get("/api/v1/divisions/draft_result")
def rest_divisions_draft_result(
    db: DbSession, current_user: CurrentUser, divisionID: int
):
    """REST endpoint: Get draft result for a division."""
    RequestContext.set_datetime()
    try:
        items = DraftResultAction.execute(db, divisionID, user_id=current_user)
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type="draft_result",
            resource_id_key="teamID",
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()


@router.get("/api/v1/divisions/draft_situation")
def rest_divisions_draft_situation(divisionID: int, db: DbSession):
    """REST endpoint: Get draft situation for a division."""
    RequestContext.set_datetime()
    try:
        result = DraftSituationAction.execute(db, divisionID)
        if result is None:
            raise HTTPException(status_code=404, detail="Division not found")
        return {
            "data": {"type": "divisions", "id": str(divisionID), "attributes": result},
            "meta": {
                "timestamp": RequestContext.get_datetime_iso()
            },
        }
    finally:
        RequestContext.reset()


@router.post("/api/v1/divisions/start_draft")
async def rest_divisions_start_draft(
    db: DbSession, current_user: CurrentUser, divisionID: int
):
    """REST endpoint: Start the draft for a division (commissioner only)."""
    RequestContext.set_datetime()
    try:
        dh, auth_err = _auth_helper(db, current_user, divisionID)
        if auth_err:
            raise auth_err
        dh.start()
        return _draft_response(divisionID, dh.draft_values)
    finally:
        RequestContext.reset()


@router.post("/api/v1/divisions/pause_draft")
async def rest_divisions_pause_draft(
    db: DbSession, current_user: CurrentUser, divisionID: int
):
    """REST endpoint: Pause the draft for a division (commissioner only)."""
    RequestContext.set_datetime()
    try:
        dh, auth_err = _auth_helper(db, current_user, divisionID)
        if auth_err:
            raise auth_err
        dh.pause()
        return _draft_response(divisionID, dh.draft_values)
    finally:
        RequestContext.reset()


@router.post("/api/v1/divisions/restart_draft")
async def rest_divisions_restart_draft(
    db: DbSession, current_user: CurrentUser, divisionID: int
):
    """REST endpoint: Restart the draft for a division (commissioner only)."""
    RequestContext.set_datetime()
    try:
        dh, auth_err = _auth_helper(db, current_user, divisionID)
        if auth_err:
            raise auth_err
        dh.restart()
        return _draft_response(divisionID, dh.draft_values)
    finally:
        RequestContext.reset()


@router.get("/api/v1/divisions/transactions-detail")
def rest_divisions_transactions_detail(db: DbSession, divisionID: int | None = None):
    """REST endpoint: Get transaction details for division (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        if divisionID is None:
            return JsonApiSerializer.serialize_error(
                400, "Bad Request", "divisionID is required"
            )
        items = DivisionsTransactionsDetailAction.execute(db, divisionID)
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type="divisions",
            resource_id_key="divisionID",
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()


@router.post("/api/v1/divisions/pusher_webhook")
async def rest_divisions_pusher_webhook(request: Request, db: DbSession):
    """Pusher webhook: update draftingUsers when members join/leave presence channels."""
    body = await request.body()
    key = request.headers.get("X-Pusher-Key", "")
    signature = request.headers.get("X-Pusher-Signature", "")

    webhook = pusher_service.get_client().validate_webhook(
        key, signature, body.decode("utf-8")
    )
    if webhook is None:
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    sequence = webhook.get("time_ms", 0)

    for event in webhook.get("events", []):
        channel = event.get("channel", "")
        name = event.get("name", "")
        user_id = event.get("user_id")

        if not channel.startswith("presence-draft-") or user_id is None:
            continue
        if name not in ("member_added", "member_removed"):
            continue

        try:
            division_id = int(channel.removeprefix("presence-draft-"))
        except ValueError:
            continue

        _update_drafting_users(
            db, division_id, int(user_id), name == "member_added", sequence
        )

    return {"status": "ok"}


class DivisionsUpdateRequest(BaseModel):
    draftType: str | None = None
    draftDate: datetime | None = None
    draftCompleteDate: datetime | None = None


@router.patch("/api/v1/divisions/{division_id}")
async def rest_divisions_update(
    division_id: int,
    payload: DivisionsUpdateRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    """Update editable division settings (division or league commissioner only)."""
    RequestContext.set_datetime()
    try:
        require_authentication(current_user)
        values = DivisionsUpdateAction.execute(
            db,
            division_id=division_id,
            user_id=current_user,
            draft_type=payload.draftType,
            draft_date=payload.draftDate,
            draft_complete_date=payload.draftCompleteDate,
        )
        return {
            "data": {
                "type": "divisions",
                "id": str(division_id),
                "attributes": values,
            },
            "meta": {
                "timestamp": RequestContext.get_datetime_iso()
            },
        }
    finally:
        RequestContext.reset()


def _update_drafting_users(
    db: Session, division_id: int, user_id: int, online: bool, sequence: int
) -> None:
    division = db.get(Division, division_id)
    if division is None:
        return
    raw = division.draftingUsers
    try:
        data = json.loads(raw) if isinstance(raw, str) else (raw or {})
    except (json.JSONDecodeError, TypeError):
        data = {}
    key = str(user_id)
    if online:
        data[key] = [1, sequence]
    elif key in data:
        del data[key]
    division.draftingUsers = json.dumps(data)
    db.commit()
