from fastapi import APIRouter, Form, Query

from app.actions.leagues import LeaguesReadListAction
from app.context import RequestContext
from app.database import DbSession
from app.utils import JsonApiSerializer

router = APIRouter(tags=["leagues"])


@router.post("/eff/eff_api/Leagues.php")
async def legacy_leagues(
    db: DbSession,
    f: str = Query(..., description="Action name"),
    userID: int = Form(...),
    season: int | None = Form(None),
):
    """Legacy PHP-compatible endpoint for Leagues actions."""
    RequestContext.set_datetime()

    try:
        if f == "ReadList":
            items = LeaguesReadListAction.execute(db, userID, season)
            return {
                "table": "Leagues",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items]
            }
        else:
            return {"error": f"Unknown action: {f}"}
    finally:
        RequestContext.reset()


@router.get("/api/v1/leagues")
def rest_leagues(db: DbSession, userID: int | None= None, season: int | None = None):
    """REST endpoint: Get leagues for user (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        items = LeaguesReadListAction.execute(db, userID, season)
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='leagues',
            resource_id_key='leagueID',
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()
