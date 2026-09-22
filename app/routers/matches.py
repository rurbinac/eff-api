from fastapi import APIRouter, Form, Query
from pydantic import BaseModel

from app.actions.matches import MatchesReadListAction
from app.context import RequestContext
from app.database import CurrentUser, DbSession
from app.exceptions import EFFException, UnknownActionException
from app.guards import require_authentication, require_pos_int
from app.utils import JsonApiSerializer
from app.utils.returns import return_error, return_many_legacy

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
        require_authentication(current_user)
        if f == "ReadList":
            if type == "byLeagueID":
                require_pos_int(leagueID, "leagueID", f"{f}({type})")
                items = MatchesReadListAction.execute(
                    db,
                    user_id=current_user,
                    league_id=leagueID,
                )
            elif type == "byDivisionID":
                require_pos_int(divisionID, "divisionID", f"{f}({type})")
                items = MatchesReadListAction.execute(
                    db,
                    user_id=current_user,
                    division_id=divisionID,
                )
            else:
                raise UnknownActionException(f, type)
            return return_many_legacy("Matches", items)
        else:
            raise UnknownActionException(f)
    except EFFException as e:
        return return_error(e)
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
