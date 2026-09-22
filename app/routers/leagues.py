from fastapi import APIRouter, Form, Query
from pydantic import BaseModel

from app.actions.leagues import (
    LeaguesBuildAction,
    LeaguesJoinAction,
    LeaguesReadListAction,
)
from app.context import RequestContext
from app.database import CurrentUser, DbSession
from app.exceptions import EFFException, NotFoundException, UnknownActionException
from app.guards import require_authentication
from app.models import User
from app.utils import JsonApiSerializer
from app.utils.legacy_returns import return_error, return_many_legacy, return_one_legacy

router = APIRouter(tags=["leagues"])


@router.post("/eff/eff_api/Leagues.php")
async def legacy_leagues(
    db: DbSession,
    current_user: CurrentUser,
    f: str = Query(..., description="Action name"),
    type: str | None = Form(None, alias="_type"),
    season: int | None = Form(None),
    # Build params
    leagueName: str | None = Form(None),
    leaguePassword: str | None = Form(None),
    leagueType: int | None = Form(None),
    gameType: int | None = Form(None),
    scoringSystem: int | None = Form(None),
    tradeDeadline: str | None = Form(None),
    publishLeague: int | None = Form(None),
    seasonStatus: int | None = Form(None),
    teamsPerDivision: str | None = Form(None),
    # Join params
    leagueID: int | None = Form(None),
):
    """Legacy PHP-compatible endpoint for Leagues actions."""
    RequestContext.set_datetime()

    try:
        require_authentication(current_user)
        if f == "ReadList":
            if type == "byUserID":

                items = LeaguesReadListAction.execute(db, current_user, season)
                return return_many_legacy("Leagues", items)
            else:
                raise UnknownActionException(f, type)

        elif f == "Build":
            user = db.query(User).filter(User.userID == current_user).first()
            if not user:
                raise NotFoundException("User", current_user)
            league_data = LeaguesBuildAction.execute(
                db=db,
                user_id=current_user,
                user_name=user.userName,
                league_name=leagueName,
                league_password=leaguePassword,
                league_type=leagueType,
                game_type=gameType,
                scoring_system=scoringSystem,
                trade_deadline=tradeDeadline,
                publish_league=publishLeague,
                season_status=seasonStatus,
                teams_per_division=teamsPerDivision,
            )
            return return_one_legacy("Leagues", league_data)

        elif f == "Join":
            team_data = LeaguesJoinAction.execute(
                db=db,
                user_id=current_user,
                league_id=leagueID,
                league_password=leaguePassword,
            )
            return return_one_legacy("Teams", team_data)

        else:
            raise UnknownActionException(f)

    except EFFException as e:
        return return_error(e)
    finally:
        RequestContext.reset()


class LeaguesBuildRequest(BaseModel):
    leagueName: str
    leaguePassword: str
    leagueType: int
    gameType: int
    scoringSystem: int
    tradeDeadline: str
    publishLeague: int
    seasonStatus: int
    teamsPerDivision: str


class LeaguesJoinRequest(BaseModel):
    leagueID: int
    leaguePassword: str


@router.get("/api/v1/leagues")
def rest_leagues(db: DbSession, userID: int | None = None, season: int | None = None):
    """REST endpoint: Get leagues for user (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        items = LeaguesReadListAction.execute(db, userID, season)
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type="leagues",
            resource_id_key="leagueID",
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()


@router.post("/api/v1/leagues/build")
def rest_leagues_build(
    payload: LeaguesBuildRequest, db: DbSession, current_user: CurrentUser
):
    """REST endpoint: Build a new league."""
    RequestContext.set_datetime()
    try:
        require_authentication(current_user)
        user = db.query(User).filter(User.userID == current_user).first()
        if not user:
            raise NotFoundException("User", current_user)
        return LeaguesBuildAction.execute(
            db=db,
            user_id=current_user,
            user_name=user.userName,
            league_name=payload.leagueName,
            league_password=payload.leaguePassword,
            league_type=payload.leagueType,
            game_type=payload.gameType,
            scoring_system=payload.scoringSystem,
            trade_deadline=payload.tradeDeadline,
            publish_league=payload.publishLeague,
            season_status=payload.seasonStatus,
            teams_per_division=payload.teamsPerDivision,
        )
    finally:
        RequestContext.reset()


@router.post("/api/v1/leagues/join")
def rest_leagues_join(
    payload: LeaguesJoinRequest, db: DbSession, current_user: CurrentUser
):
    """REST endpoint: Join an existing league."""
    RequestContext.set_datetime()
    try:
        require_authentication(current_user)
        return LeaguesJoinAction.execute(
            db=db,
            user_id=current_user,
            league_id=payload.leagueID,
            league_password=payload.leaguePassword,
        )
    finally:
        RequestContext.reset()
