from fastapi import APIRouter, Depends, Request, Query, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.actions.divisions import DivisionsReadListAction, DivisionsTransactionsDetailAction
from app.context import RequestContext

router = APIRouter(tags=["divisions"])


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
        else:
            return {"error": f"Unknown action: {f}"}, 400
    finally:
        RequestContext.reset()


@router.post("/api/divisions/readlist")
def rest_divisions(leagueID: int, db: Session = Depends(get_db)):
    """REST endpoint: Get divisions for league."""
    RequestContext.set_datetime()
    try:
        items = DivisionsReadListAction.execute(db, leagueID)
        return items
    finally:
        RequestContext.reset()


@router.post("/api/divisions/transactions-detail")
def rest_divisions_transactions_detail(divisionID: int, db: Session = Depends(get_db)):
    """REST endpoint: Get transaction details for division."""
    RequestContext.set_datetime()
    try:
        items = DivisionsTransactionsDetailAction.execute(db, divisionID)
        return items
    finally:
        RequestContext.reset()
