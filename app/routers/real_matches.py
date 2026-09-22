from fastapi import APIRouter, Form, Query
from pydantic import BaseModel

from app.actions.real_matches import RealMatchesReadListAction
from app.context import RequestContext
from app.database import CurrentUser, DbSession
from app.exceptions import EFFException, UnknownActionException
from app.guards import require_authentication, require_pos_int
from app.utils import JsonApiSerializer
from app.utils.returns import return_error, return_many_legacy

router = APIRouter(tags=["real-matches"])


class RealMatchesRequest(BaseModel):
    realCompetitionID: int
    realCompetitionSeasonID: int


@router.post("/eff/eff_api/RealMatches.php")
async def legacy_real_matches(
    db: DbSession,
    current_user: CurrentUser,
    f: str = Query(...),
    type: str | None = Form(None, alias="_type"),
    realCompetitionID: int | None = Form(None),
    realCompetitionMatchDay: int | None = Form(None),
):
    """Legacy PHP-compatible RealMatches endpoint."""
    RequestContext.set_datetime()
    try:
        require_authentication(current_user)
        if f == "ReadList":
            if type == "byMatchDay":
                require_pos_int(realCompetitionID, "realCompetitionID", f"{f}({type})")
                require_pos_int(realCompetitionMatchDay, "realCompetitionMatchDay", f"{f}({type})")
                items = RealMatchesReadListAction.execute(
                    db,
                    real_competition_id=realCompetitionID,
                    real_competition_match_day=realCompetitionMatchDay,
                )
            else:
                raise UnknownActionException(f, type)
            return return_many_legacy("RealMatches", items)
        else:
            raise UnknownActionException(f)
    except EFFException as e:
        return return_error(e)
    finally:
        RequestContext.reset()


@router.get("/api/v1/real_matches")
async def rest_real_matches(
    payload: RealMatchesRequest,
    db: DbSession,
):
    """REST endpoint for RealMatches ReadList (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        items = RealMatchesReadListAction.execute(
            db,
            real_competition_id=payload.realCompetitionID,
            real_competition_season_id=payload.realCompetitionSeasonID,
        )
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='real-matches',
            resource_id_key='realMatchID',
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()
