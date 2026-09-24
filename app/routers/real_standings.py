from fastapi import APIRouter, Form, Query
from pydantic import BaseModel

from app.actions.real_standings import RealStandingsReadListAction
from app.context import RequestContext
from app.database import CurrentUser, DbSession
from app.exceptions import EFFException, UnknownActionException
from app.guards import require_authentication
from app.utils import JsonApiSerializer
from app.utils.legacy_returns import return_error, return_many_legacy

router = APIRouter(tags=["real-standings"])


class RealStandingsRequest(BaseModel):
    realCompetitionID: int
    realCompetitionMatchDay: int
    divisionID: int | None = None


@router.post("/eff/eff_api/RealStandings.php")
async def legacy_real_standings(
    db: DbSession,
    current_user: CurrentUser,
    f: str = Query(...),
    realCompetitionID: int | None = Form(None),
    realCompetitionMatchDay: int | None = Form(None),
    divisionID: int | None = Form(None),
    realTeamMemberKey: str | None = Form(None),
    type: str | None = Form(None, alias="_type"),
    include: str | None = Form(None, alias="_include"),
):
    """Legacy PHP-compatible RealStandings endpoint."""
    RequestContext.set_datetime()
    try:
        require_authentication(current_user)
        if f == "ReadList":
            if type == "byDivisionID":
                items = RealStandingsReadListAction.execute(
                    db,
                    real_competition_id=realCompetitionID,
                    real_competition_match_day=realCompetitionMatchDay,
                    division_id=divisionID,
                )
            elif type == "byRealTeamMemberKey":
                include_list = [f.strip() for f in include.split(",")] if include else None
                items = RealStandingsReadListAction.execute_by_member_key(
                    db,
                    real_competition_id=realCompetitionID,
                    real_team_member_key=realTeamMemberKey,
                    include=include_list,
                )
            else:
                raise UnknownActionException(f, type)
            return return_many_legacy("RealStandings", items)
        else:
            raise UnknownActionException(f)
    except EFFException as e:
        return return_error(e)
    finally:
        RequestContext.reset()


@router.get("/api/v1/real_standings")
async def rest_real_standings(
    payload: RealStandingsRequest,
    db: DbSession,
):
    """REST endpoint for RealStandings ReadList (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        items = RealStandingsReadListAction.execute(
            db,
            real_competition_id=payload.realCompetitionID,
            real_competition_match_day=payload.realCompetitionMatchDay,
            division_id=payload.divisionID,
        )
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='real-standings',
            resource_id_key='realStandingID',
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()
