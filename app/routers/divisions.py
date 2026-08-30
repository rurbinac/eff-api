import json
from datetime import datetime

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
from app.models import Division
from app.services import pusher as pusher_service
from app.utils import JsonApiSerializer

router = APIRouter(tags=["divisions"])


def _auth_helper(db: Session, user_id: int | None, division_id: int) -> tuple[DraftHelper, HTTPException | None]:
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
            }
        },
        "meta": {"timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S")}
    }


@router.post("/eff/eff_api/Divisions.php")
async def legacy_divisions(
    db: DbSession,
    current_user: CurrentUser,
    f: str = Query(..., description="Action name"),
    leagueID: int | None = Form(None),
    divisionID: int | None = Form(None),
    draftType: str | None = Form(None),
    draftDate: datetime | None = Form(None),
    draftCompleteDate: datetime | None = Form(None),
):
    """Legacy PHP-compatible endpoint for Divisions actions."""
    RequestContext.set_datetime()

    try:
        if f == "ReadList":
            if leagueID is None:
                return {"error": "leagueID is required for ReadList"}, 400
            items = DivisionsReadListAction.execute(db, leagueID)
            return {
                "table": "Divisions",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items]
            }
        elif f == "TransactionsDetail":
            if divisionID is None:
                return {"error": "divisionID is required for TransactionsDetail"}, 400
            items = DivisionsTransactionsDetailAction.execute(db, divisionID)
            return {
                "table": "TransactionsDetail",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items]
            }
        elif f == "DraftResult":
            if divisionID is None:
                return {"error": "divisionID is required for DraftResult"}, 400
            items = DraftResultAction.execute(db, divisionID, user_id=current_user)
            return {
                "table": "DraftResult",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items]
            }
        elif f == "DraftSituation":
            if divisionID is None:
                return {"error": "divisionID is required for DraftSituation"}
            result = DraftSituationAction.execute(db, divisionID)
            if result is None:
                return {"error": "Division not found"}
            return {
                "table": "DraftSituation",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "values": result
            }
        elif f in ("StartDraft", "PauseDraft", "RestartDraft"):
            if divisionID is None:
                return {"error": f"divisionID is required for {f}"}
            dh, auth_err = _auth_helper(db, current_user, divisionID)
            if auth_err:
                return {"error": auth_err.detail}
            try:
                action = {"StartDraft": dh.start, "PauseDraft": dh.pause, "RestartDraft": dh.restart}[f]
                action()
            except DraftException as e:
                return PlainTextResponse(e.legacy_response(), status_code=e.status_code)
            dv = dh.draft_values
            return {
                "table": f,
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "values": {
                    "divisionID": divisionID,
                    "draftStatus": dv.division.get("draftStatus"),
                    "draftingStart": dv.division.get("draftingStart"),
                    "draftingLimit": dv.division.get("draftingLimit"),
                }
            }
        elif f == "Update":
            if divisionID is None:
                return {"error": "divisionID is required for Update"}
            if current_user is None:
                return {"error": "Authentication required"}, 401
            try:
                values = DivisionsUpdateAction.execute(
                    db,
                    division_id=divisionID,
                    user_id=current_user,
                    draft_type=draftType,
                    draft_date=draftDate,
                    draft_complete_date=draftCompleteDate,
                )
            except HTTPException as e:
                return {"error": e.detail}, e.status_code
            return {
                "table": "Divisions",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "values": values,
            }
        else:
            return {"error": f"Unknown action: {f}"}, 400
    finally:
        RequestContext.reset()


@router.get("/api/v1/divisions")
def rest_divisions(db: DbSession, leagueID: int | None = None):
    """REST endpoint: Get divisions for league (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        if leagueID is None:
            return JsonApiSerializer.serialize_error(400, "Bad Request", "leagueID is required")
        items = DivisionsReadListAction.execute(db, leagueID)
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='divisions',
            resource_id_key='divisionID',
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()


@router.get("/api/v1/divisions/draft_result")
def rest_divisions_draft_result(db: DbSession, current_user: CurrentUser, divisionID: int):
    """REST endpoint: Get draft result for a division."""
    RequestContext.set_datetime()
    try:
        items = DraftResultAction.execute(db, divisionID, user_id=current_user)
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='draft_result',
            resource_id_key='teamID',
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
            "meta": {"timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S")}
        }
    finally:
        RequestContext.reset()


@router.post("/api/v1/divisions/start_draft")
async def rest_divisions_start_draft(db: DbSession, current_user: CurrentUser, divisionID: int):
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
async def rest_divisions_pause_draft(db: DbSession, current_user: CurrentUser, divisionID: int):
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
async def rest_divisions_restart_draft(db: DbSession, current_user: CurrentUser, divisionID: int):
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
            return JsonApiSerializer.serialize_error(400, "Bad Request", "divisionID is required")
        items = DivisionsTransactionsDetailAction.execute(db, divisionID)
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='divisions',
            resource_id_key='divisionID',
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

    webhook = pusher_service.get_client().validate_webhook(key, signature, body.decode("utf-8"))
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

        _update_drafting_users(db, division_id, int(user_id), name == "member_added", sequence)

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
        if current_user is None:
            raise HTTPException(status_code=401, detail="Authentication required")
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
            "meta": {"timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S")},
        }
    finally:
        RequestContext.reset()


def _update_drafting_users(db: Session, division_id: int, user_id: int, online: bool, sequence: int) -> None:
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
