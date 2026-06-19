from fastapi import APIRouter, Query, Form, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.context import RequestContext
from app.actions.matches import MatchesReadListAction
from app.utils import JsonApiSerializer

router = APIRouter(tags=["matches"])


class MatchesRequest(BaseModel):
    leagueID: int | None = None
    divisionID: int | None = None
    teamID: int | None = None


@router.post("/eff/eff_api/Matches.php")
async def legacy_matches(
    f: str = Query(...),
    format: str | None = Query("json", alias="_format"),
    type: str | None = Query(None, alias="_type"),
    leagueID: int | None = Form(None),
    divisionID: int | None = Form(None),
    teamID: int | None = Form(None),
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible Matches endpoint."""
    RequestContext.set_datetime()
    try:
        if f == "ReadList":
            items = MatchesReadListAction.execute(
                db,
                league_id=leagueID,
                division_id=divisionID,
                team_id=teamID
            )
            return {
                "table": "Matches",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items]
            }
        else:
            return {"error": f"Unknown function: {f}"}, 400
    finally:
        RequestContext.reset()


@router.get("/api/v1/matches")
async def rest_matches(
    payload: MatchesRequest,
    db: Session = Depends(get_db),
):
    """REST endpoint for Matches ReadList (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        items = MatchesReadListAction.execute(
            db,
            league_id=payload.leagueID,
            division_id=divisionID,
            team_id=payload.teamID
        )
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='matches',
            resource_id_key='matchID',
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()
