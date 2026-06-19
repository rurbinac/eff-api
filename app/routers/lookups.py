from fastapi import APIRouter, Query, Form, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.context import RequestContext
from app.actions.lookups import LookupsReadListAction
from app.actions.top_epl import TopEPLAction
from app.utils import JsonApiSerializer


class LookupsRequest(BaseModel):
    lookupType: int


router = APIRouter(tags=["lookups"])


@router.post("/eff/eff_api/Lookups.php")
async def legacy_lookups(
    f: str = Query(...),
    format: str | None = Query("json", alias="_format"),
    type: str | None = Query(None, alias="_type"),
    lookupType: int | None = Form(None),
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible Lookups endpoint."""
    RequestContext.set_datetime()
    try:
        if f == "ReadList":
            items = LookupsReadListAction.execute(db, lookup_num=lookupType)
            return {
                "table": "Lookups",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items]
            }
        else:
            return {"error": f"Unknown function: {f}"}, 400
    finally:
        RequestContext.reset()


@router.get("/api/v1/lookups")
async def rest_lookups(
    lookupType: int | None = None,
    db: Session = Depends(get_db),
):
    """REST endpoint for Lookups ReadList (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        items = LookupsReadListAction.execute(db, lookup_num=lookupType)
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='lookups',
            resource_id_key='lookupID',
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()


@router.get("/api/v1/top_epl")
async def rest_top_epl(
    limit: int | None = 4,
    db: Session = Depends(get_db),
):
    """REST endpoint: Get top EPL teams by standings (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        data = TopEPLAction.execute(db, limit=limit or 4)
        return data
    finally:
        RequestContext.reset()
