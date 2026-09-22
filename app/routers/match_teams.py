from fastapi import APIRouter, Form, Query
from pydantic import BaseModel

from app.actions.match_teams import (
    ClearLineupByMatchTeamIDAction,
    GetLineupByCompetitionTypeAction,
    GetLineupByMatchTeamIDAction,
    GetScoresByMatchDayAction,
    GetScoresByMatchIDsAction,
    MatchTeamsReadListAction,
    SetLineupByCompetitionTypeAction,
)
from app.constants import CompetitionTypeConstants
from app.context import RequestContext
from app.database import CurrentUser, DbSession
from app.exceptions import (
    EFFException,
    NotFoundException,
    UnauthorizedException,
    UnknownActionException,
)
from app.guards import (
    require_authentication,
    require_in_list,
    require_league_member,
    require_pos_int,
    require_pos_ints,
    require_team_owner,
    require_value,
)
from app.utils import JsonApiSerializer
from app.utils.returns import return_error, return_many_legacy, return_one_legacy

router = APIRouter(tags=["match-teams"])


class MatchTeamsRequest(BaseModel):
    matchID: int


@router.post("/eff/eff_api/MatchTeams.php")
async def legacy_match_teams(
    db: DbSession,
    current_user: CurrentUser,
    f: str = Query(...),
    type: str | None = Form(None, alias="_type"),
    matchID: int | None = Form(None),
    matchTeamID: int | None = Form(None),
    teamID: int | None = Form(None),
    competitionType: int | None = Form(None),
    competitionMatchDay: int | None = Form(None),
    matchIDs: str | None = Form(None),
    leagueID: int | None = Form(None),
    divisionID: int | None = Form(None),
    realTeamID: int | None = Form(None),
    realPlayerIDs: str | None = Form(None),
    substituteRealPlayerIDs: str | None = Form(None),
):
    """Legacy PHP-compatible MatchTeams endpoint."""
    RequestContext.set_datetime()
    try:
        require_authentication(current_user)
        if f == "ReadList":
            if type == "byTeamID":
                teamID = require_pos_int(teamID, "teamID", f)
                require_league_member(db, current_user, team_id=teamID)
                items = MatchTeamsReadListAction.execute(db, team_id=teamID)
            else:
                raise UnknownActionException(f, type)
            return return_many_legacy("MatchTeams", items)
        elif f == "GetLineupByMatchTeamID":
            matchTeamID = require_value(matchTeamID, "matchTeamID", f)
            result = GetLineupByMatchTeamIDAction.execute(db, match_team_id=matchTeamID)
            if result is None:
                raise NotFoundException("Lineup", matchTeamID)
            return return_many_legacy("MatchTeams", result)
        elif f == "GetLineupByCompetitionType":
            teamID = require_pos_int(teamID, "teamID", f)
            require_league_member(db, current_user, team_id=teamID)
            competitionMatchDay = require_pos_int(competitionMatchDay, "competitionMatchDay", f)
            competitionType = require_pos_int(competitionType, "competitionType", f)
            competitionType = require_in_list(competitionType, CompetitionTypeConstants.valid_values(), "competitionType", f)
            result = GetLineupByCompetitionTypeAction.execute(
                db,
                team_id=teamID,
                competition_type=competitionType,
                competition_match_day=competitionMatchDay,
            )
            return return_many_legacy("MatchTeams", result or [])
        elif f == "SetLineupByCompetitionType":
            teamID = require_pos_int(teamID, "teamID", f)
            require_team_owner(db, current_user, teamID)
            competitionMatchDay = require_pos_int(competitionMatchDay, "competitionMatchDay", f)
            competitionType = require_pos_int(competitionType, "competitionType", f)
            competitionType = require_in_list(competitionType, CompetitionTypeConstants.valid_values(), "competitionType", f)
            realTeamID = require_pos_int(realTeamID, "realTeamID", f, not_empty=False)
            realPlayerIDs = require_pos_ints(realPlayerIDs, "realPlayerIDs", f, not_empty=False)
            substituteRealPlayerIDs = require_pos_ints(substituteRealPlayerIDs, "substituteRealPlayerIDs", f, not_empty=False)
            result = SetLineupByCompetitionTypeAction.execute(
                db,
                team_id=teamID,
                competition_type=competitionType,
                competition_match_day=competitionMatchDay,
                real_team_id=realTeamID,
                real_player_ids=realPlayerIDs,
                substitute_real_player_ids=substituteRealPlayerIDs,
            )
            if result is None:
                raise NotFoundException("Lineup", teamID)
            return return_many_legacy("MatchTeams", result)
        elif f == "ClearLineupByMatchTeamID":
            require_value(matchTeamID, "matchTeamID", f)
            try:
                result = ClearLineupByMatchTeamIDAction.execute(db, match_team_id=matchTeamID, user_id=current_user)
            except PermissionError:
                raise UnauthorizedException()
            if result is None:
                raise NotFoundException("Lineup", matchTeamID)
            return return_one_legacy("MatchTeams", result)
        elif f == "GetScoresByMatchDay":
            require_in_list(competitionType, CompetitionTypeConstants.valid_values(), "competitionType", f)
            require_value(competitionMatchDay, "competitionMatchDay", f)
            require_value(leagueID, "leagueID", f)
            result = GetScoresByMatchDayAction.execute(
                db,
                competition_type=competitionType,
                competition_match_day=competitionMatchDay,
                league_id=leagueID,
                division_id=divisionID,
            )
            if result is None:
                raise NotFoundException("Scores", competitionMatchDay)
            return return_many_legacy("MatchTeams", result)
        elif f == "GetScoresByMatchIDs":
            ids = require_pos_ints(matchIDs, "matchIDs", f)
            result = GetScoresByMatchIDsAction.execute(db, match_ids=ids)
            if result is None:
                raise NotFoundException("Scores", None)
            return return_many_legacy("MatchTeams", result)
        else:
            raise UnknownActionException(f)
    except EFFException as e:
        return return_error(e)
    finally:
        RequestContext.reset()


@router.get("/api/v1/match_teams")
async def rest_match_teams(
    payload: MatchTeamsRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    """REST endpoint for MatchTeams ReadList (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        require_authentication(current_user)
        require_league_member(db, current_user, team_id=payload.matchID)
        items = MatchTeamsReadListAction.execute(db, team_id=payload.matchID)
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='match-teams',
            resource_id_key='matchTeamID',
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()
