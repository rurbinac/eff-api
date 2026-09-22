from fastapi import APIRouter, Form, HTTPException, Query
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
from app.context import RequestContext
from app.database import CurrentUser, DbSession
from app.exceptions import UnknownActionException
from app.guards import require_pos_int, require_pos_ints, require_value
from app.utils import JsonApiSerializer

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
        if f == "ReadList":
            if type == "byTeamID":
                require_pos_int(teamID, "teamID", f)
                return MatchTeamsReadListAction.execute(db, team_id=teamID)
            else:
                raise UnknownActionException(f, type)
        elif f == "GetLineupByMatchTeamID":
            require_value(matchTeamID, "matchTeamID", f)
            result = GetLineupByMatchTeamIDAction.execute(db, match_team_id=matchTeamID)
            if result is None:
                raise HTTPException(status_code=404, detail="Not found")
            return result
        elif f == "GetLineupByCompetitionType":
            require_value(teamID, "teamID", f)
            require_value(competitionType, "competitionType", f)
            require_value(competitionMatchDay, "competitionMatchDay", f)
            result = GetLineupByCompetitionTypeAction.execute(
                db,
                team_id=teamID,
                competition_type=competitionType,
                competition_match_day=competitionMatchDay,
            )
            # None means no MatchTeam exists for these params — return empty items
            # (unlike GetLineupByMatchTeamID where a missing specific ID is a 404)
            if result is None:
                result = {
                    "table": "MatchTeams",
                    "timestamp": RequestContext.get_datetime_iso(),
                    "items": [],
                }
            return result
        elif f == "SetLineupByCompetitionType":
            require_value(teamID, "teamID", f)
            require_value(competitionType, "competitionType", f)
            require_value(competitionMatchDay, "competitionMatchDay", f)
            require_value(realTeamID, "realTeamID", f)
            require_value(realPlayerIDs, "realPlayerIDs", f)
            player_ids = require_pos_ints(realPlayerIDs, "realPlayerIDs", f)
            sub_ids = require_pos_ints(substituteRealPlayerIDs, "substituteRealPlayerIDs", f) if substituteRealPlayerIDs else []
            result = SetLineupByCompetitionTypeAction.execute(
                db,
                team_id=teamID,
                competition_type=competitionType,
                competition_match_day=competitionMatchDay,
                real_team_id=realTeamID,
                real_player_ids=player_ids,
                substitute_real_player_ids=sub_ids,
            )
            if result is None:
                raise HTTPException(status_code=404, detail="Not found")
            return result
        elif f == "ClearLineupByMatchTeamID":
            require_value(matchTeamID, "matchTeamID", f)
            require_value(current_user, "token", f)
            try:
                result = ClearLineupByMatchTeamIDAction.execute(db, match_team_id=matchTeamID, user_id=current_user)
            except PermissionError:
                raise HTTPException(status_code=401, detail="Unauthorized")
            if result is None:
                raise HTTPException(status_code=404, detail="Not found")
            return result
        elif f == "GetScoresByMatchDay":
            require_value(competitionType, "competitionType", f)
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
                raise HTTPException(status_code=404, detail="Not found")
            return result
        elif f == "GetScoresByMatchIDs":
            ids = require_pos_ints(matchIDs, "matchIDs", f)
            return GetScoresByMatchIDsAction.execute(db, match_ids=ids)
        else:
            raise UnknownActionException(f)
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
        items = MatchTeamsReadListAction.execute(db, team_id=payload.matchID, user_id=current_user)
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='match-teams',
            resource_id_key='matchTeamID',
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()
