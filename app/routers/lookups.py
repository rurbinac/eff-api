from fastapi import APIRouter, Query, Form, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.context import RequestContext
from app.actions.lookups import LookupsReadListAction

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


@router.post("/api/lookups/readlist")
async def rest_lookups(
    lookupType: int,
    db: Session = Depends(get_db),
):
    """REST endpoint for Lookups ReadList."""
    RequestContext.set_datetime()
    try:
        items = LookupsReadListAction.execute(db, lookup_num=lookupType)
        return items
    finally:
        RequestContext.reset()
