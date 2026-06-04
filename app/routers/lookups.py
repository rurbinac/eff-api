from fastapi import APIRouter, Query, Form, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import SessionLocal
from app.context import RequestContext
from app.actions.lookups import LookupsReadListAction


class LookupsReadListRequest(BaseModel):
    lookupNum: int | None = None

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/eff/eff_api/Lookups.php")
async def legacy_lookups(
    f: str = Query(...),
    format: str = Form("json", alias="_format"),
    type: str = Form(None, alias="_type"),
    lookupNum: int = Form(None),
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible Lookups endpoint."""
    RequestContext.set_datetime()
    try:
        if f == "ReadList":
            if type == "byLookupNum" and lookupNum is not None:
                return LookupsReadListAction.execute(db, lookup_num=lookupNum)
            else:
                # Return all lookups if no filter specified
                return LookupsReadListAction.execute(db)
        else:
            return {"error": f"Unknown function: {f}"}
    finally:
        RequestContext.reset()


@router.post("/api/lookups/readlist")
async def rest_lookups(
    payload: LookupsReadListRequest,
    db: Session = Depends(get_db),
):
    """REST endpoint for Lookups ReadList."""
    RequestContext.set_datetime()
    try:
        return LookupsReadListAction.execute(db, lookup_num=payload.lookupNum)
    finally:
        RequestContext.reset()
