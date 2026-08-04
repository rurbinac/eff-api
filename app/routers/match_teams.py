from fastapi import APIRouter, Depends, Form, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.actions.match_teams import (
    GetLineupByCompetitionTypeAction,
    GetLineupByMatchTeamIDAction,
    GetScoresByMatchIDsAction,
    MatchTeamsReadListAction,
)
from app.context import RequestContext
from app.database import get_db
from app.utils import JsonApiSerializer

router = APIRouter(tags=["match-teams"])


class MatchTeamsRequest(BaseModel):
    matchID: int


@router.post("/eff/eff_api/MatchTeams.php")
async def legacy_match_teams(
    f: str = Query(...),
    format: str | None = Query("json", alias="_format"),
    type: str | None = Query(None, alias="_type"),
    matchID: int | None = Form(None),
    matchTeamID: int | None = Form(None),
    teamID: int | None = Form(None),
    competitionType: int | None = Form(None),
    competitionMatchDay: int | None = Form(None),
    matchIDs: str | None = Form(None),
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible MatchTeams endpoint."""
    RequestContext.set_datetime()
    try:
        if f == "ReadList":
            items = MatchTeamsReadListAction.execute(db, match_id=matchID)
            return {
                "table": "MatchTeams",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items]
            }
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
    db: Session = Depends(get_db),
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
