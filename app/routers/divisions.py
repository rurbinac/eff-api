from fastapi import APIRouter, Depends, HTTPException, Request, Query, Form
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.actions.divisions import DivisionsReadListAction, DivisionsTransactionsDetailAction
from app.actions.draft import DraftResultAction, DraftSituationAction
from app.actions.draft.draft_exception import DraftException
from app.actions.draft.draft_helper import DraftHelper
from app.actions.draft.draft_values import DraftValues
from app.context import RequestContext
from app.security import decode_token
from app.utils import JsonApiSerializer


class DivisionsRequest(BaseModel):
    leagueID: int | None = None
    divisionID: int | None = None


router = APIRouter(tags=["divisions"])


def _auth_helper(request: Request, db: Session, division_id: int) -> tuple[DraftHelper, HTTPException | None]:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None, HTTPException(status_code=401, detail="Missing or invalid token")
    payload = decode_token(auth_header[7:])
    if payload is None:
        return None, HTTPException(status_code=401, detail="Invalid or expired token")
    user_id = int(payload.get("sub"))
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
    f: str = Query(..., description="Action name"),
    format: str | None = Query("json", alias="_format"),
    type: str | None = Query(None, alias="_type"),
    leagueID: int | None = Form(None),
    divisionID: int | None = Form(None),
    request: Request = None,
    db: Session = Depends(get_db),
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
            items = DraftResultAction.execute(db, divisionID)
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
            dh, auth_err = _auth_helper(request, db, divisionID)
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
        else:
            return {"error": f"Unknown action: {f}"}, 400
    finally:
        RequestContext.reset()


@router.get("/api/v1/divisions")
def rest_divisions(leagueID: int | None = None, db: Session = Depends(get_db)):
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
def rest_divisions_draft_result(divisionID: int, db: Session = Depends(get_db)):
    """REST endpoint: Get draft result for a division."""
    RequestContext.set_datetime()
    try:
        items = DraftResultAction.execute(db, divisionID)
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='draft_result',
            resource_id_key='teamID',
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()


@router.get("/api/v1/divisions/draft_situation")
def rest_divisions_draft_situation(divisionID: int, db: Session = Depends(get_db)):
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
async def rest_divisions_start_draft(request: Request, divisionID: int, db: Session = Depends(get_db)):
    """REST endpoint: Start the draft for a division (commissioner only)."""
    RequestContext.set_datetime()
    try:
        dh, auth_err = _auth_helper(request, db, divisionID)
        if auth_err:
            raise auth_err
        dh.start()
        return _draft_response(divisionID, dh.draft_values)
    finally:
        RequestContext.reset()


@router.post("/api/v1/divisions/pause_draft")
async def rest_divisions_pause_draft(request: Request, divisionID: int, db: Session = Depends(get_db)):
    """REST endpoint: Pause the draft for a division (commissioner only)."""
    RequestContext.set_datetime()
    try:
        dh, auth_err = _auth_helper(request, db, divisionID)
        if auth_err:
            raise auth_err
        dh.pause()
        return _draft_response(divisionID, dh.draft_values)
    finally:
        RequestContext.reset()


@router.post("/api/v1/divisions/restart_draft")
async def rest_divisions_restart_draft(request: Request, divisionID: int, db: Session = Depends(get_db)):
    """REST endpoint: Restart the draft for a division (commissioner only)."""
    RequestContext.set_datetime()
    try:
        dh, auth_err = _auth_helper(request, db, divisionID)
        if auth_err:
            raise auth_err
        dh.restart()
        return _draft_response(divisionID, dh.draft_values)
    finally:
        RequestContext.reset()


@router.get("/api/v1/divisions/transactions-detail")
def rest_divisions_transactions_detail(divisionID: int | None = None, db: Session = Depends(get_db)):
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
