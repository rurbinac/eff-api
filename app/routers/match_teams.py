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
from app.utils import JsonApiSerializer

router = APIRouter(tags=["match-teams"])


class MatchTeamsRequest(BaseModel):
    matchID: int


@router.post("/eff/eff_api/MatchTeams.php")
async def legacy_match_teams(
    db: DbSession,
    current_user: CurrentUser,
    f: str = Query(...),
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
            return MatchTeamsReadListAction.execute(db, team_id=teamID)
        elif f == "GetLineupByMatchTeamID":
            if matchTeamID is None:
                raise HTTPException(status_code=400, detail="matchTeamID is required")
            result = GetLineupByMatchTeamIDAction.execute(db, match_team_id=matchTeamID)
            if result is None:
                raise HTTPException(status_code=404, detail="Not found")
            return result
        elif f == "GetLineupByCompetitionType":
            if teamID is None or competitionType is None or competitionMatchDay is None:
                raise HTTPException(status_code=400, detail="teamID, competitionType, and competitionMatchDay are required")
            result = GetLineupByCompetitionTypeAction.execute(
                db,
                team_id=teamID,
                competition_type=competitionType,
                competition_match_day=competitionMatchDay,
            )
            if result is None:
                raise HTTPException(status_code=404, detail="Not found")
            return result
        elif f == "SetLineupByCompetitionType":
            if teamID is None or competitionType is None or competitionMatchDay is None or realTeamID is None or not realPlayerIDs:
                raise HTTPException(status_code=400, detail="teamID, competitionType, competitionMatchDay, realTeamID, and realPlayerIDs are required")
            player_ids = [int(i) for i in realPlayerIDs.split(",") if i.strip().isdigit()]
            sub_ids = [int(i) for i in substituteRealPlayerIDs.split(",") if i.strip().isdigit()] if substituteRealPlayerIDs else []
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
            if matchTeamID is None:
                raise HTTPException(status_code=400, detail="matchTeamID is required")
            if current_user is None:
                raise HTTPException(status_code=401, detail="Unauthorized")
            try:
                result = ClearLineupByMatchTeamIDAction.execute(db, match_team_id=matchTeamID, user_id=current_user)
            except PermissionError:
                raise HTTPException(status_code=401, detail="Unauthorized")
            if result is None:
                raise HTTPException(status_code=404, detail="Not found")
            return result
        elif f == "GetScoresByMatchDay":
            if competitionType is None or competitionMatchDay is None or leagueID is None:
                raise HTTPException(status_code=400, detail="competitionType, competitionMatchDay, and leagueID are required")
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
            if not matchIDs:
                raise HTTPException(status_code=400, detail="matchIDs is required")
            ids = [int(i) for i in matchIDs.split(",") if i.strip().isdigit()]
            if not ids:
                raise HTTPException(status_code=400, detail="matchIDs must be a comma-separated list of integers")
            return GetScoresByMatchIDsAction.execute(db, match_ids=ids)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown function: {f}")
    finally:
        RequestContext.reset()


@router.get("/api/v1/match_teams")
async def rest_match_teams(
    payload: MatchTeamsRequest,
    db: DbSession,
):
    """REST endpoint for MatchTeams ReadList (JSON:API format)."""
    RequestContext.set_datetime()
    try:
        items = MatchTeamsReadListAction.execute(db, match_id=payload.matchID)
        response = JsonApiSerializer.serialize_collection(
            items,
            resource_type='match-teams',
            resource_id_key='matchTeamID',
        )
        return JsonApiSerializer.add_timestamp(response)
    finally:
        RequestContext.reset()
