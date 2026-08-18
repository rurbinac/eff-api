from fastapi import APIRouter, Form, HTTPException, Query

from app.actions.lookups import LookupsReadListAction
from app.actions.top_epl import TopEPLAction
from app.context import RequestContext
from app.database import DbSession
from app.utils import JsonApiSerializer

router = APIRouter(tags=["lookups"])


@router.post("/eff/eff_api/Lookups.php")
async def legacy_lookups(
    db: DbSession,
    f: str = Query(...),
    lookupNum: int | None = Form(None),
):
    """Legacy PHP-compatible Lookups endpoint."""
    RequestContext.set_datetime()
    try:
        if f == "ReadList":
            items = LookupsReadListAction.execute(db, lookup_num=lookupNum)
            return {
                "table": "Lookups",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items]
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unknown function: {f}")
    finally:
        RequestContext.reset()


@router.get("/api/v1/lookups")
async def rest_lookups(
    db: DbSession,
    lookupType: int | None = None,
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
    db: DbSession,
    limit: int | None = 4,
):
    """REST endpoint: Get top EPL teams by standings (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        data = TopEPLAction.execute(db, limit=limit or 4)
        return data
    finally:
        RequestContext.reset()
