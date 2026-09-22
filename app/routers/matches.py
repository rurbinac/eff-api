from fastapi import APIRouter, Form, Query
from pydantic import BaseModel

from app.actions.matches import MatchesReadListAction
from app.context import RequestContext
from app.database import CurrentUser, DbSession
from app.exceptions import UnknownActionException
from app.guards import require_pos_int
from app.utils import JsonApiSerializer

router = APIRouter(tags=["matches"])


class MatchesRequest(BaseModel):
    leagueID: int | None = None
    divisionID: int | None = None
    teamID: int | None = None


@router.post("/eff/eff_api/Matches.php")
async def legacy_matches(
    db: DbSession,
    current_user: CurrentUser,
    f: str = Query(...),
    type: str | None = Form(None, alias="_type"),
    leagueID: int | None = Form(None),
    divisionID: int | None = Form(None),
):
    """Legacy PHP-compatible Matches endpoint."""
    RequestContext.set_datetime()
    try:
        if f == "ReadList":
            if type == "byLeagueID":
                require_pos_int(leagueID, "leagueID", f"{f}({type})")
            elif type == "byDivisionID":
                require_pos_int(divisionID, "divisionID", f"{f}({type})")
            else:
                raise UnknownActionException(f, type)
            items = MatchesReadListAction.execute(
                db,
                user_id=current_user,
                league_id=leagueID,
                division_id=divisionID,
            )
            return {
                "table": "Matches",
                "timestamp": RequestContext.get_datetime_iso(),
                "items": items,
            }
        else:
            raise UnknownActionException(f)
    finally:
        RequestContext.reset()


@router.get("/api/v1/matches")
async def rest_matches(
    db: DbSession,
    current_user: CurrentUser,
    payload: MatchesRequest,
):
    """REST endpoint for Matches ReadList (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        items = MatchesReadListAction.execute(
            db,
            user_id=current_user,
            league_id=payload.leagueID,
            division_id=payload.divisionID,
        )
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='matches',
            resource_id_key='matchID',
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()
