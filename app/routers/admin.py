import logging
import random
from datetime import datetime

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.config import settings
from app.database import CurrentUser, DbSession
from app.guards import require_admin, require_division
from app.models import Division, League, Team
from app.services.query import QueryService
from app.utils.dt import to_iso, utc_now

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin"])


# ---------------------------------------------------------------------------
# Cloud SQL backup helpers (ADMIN_TOKEN auth — for CLI/scripts)
# ---------------------------------------------------------------------------


def _check_token(authorization: str | None) -> None:
    if not settings.admin_token:
        raise HTTPException(status_code=503, detail="ADMIN_TOKEN not configured")
    if authorization != f"Bearer {settings.admin_token}":
        raise HTTPException(status_code=401, detail="Unauthorized")


def _sql_service():
    from google.auth import default
    from googleapiclient import discovery

    credentials, _ = default(scopes=["https://www.googleapis.com/auth/sqlservice.admin"])
    return discovery.build("sqladmin", "v1", credentials=credentials, cache_discovery=False)


def _parse_instance() -> tuple[str, str]:
    parts = settings.cloud_sql_instance.split(":")
    if len(parts) != 3:
        raise HTTPException(status_code=503, detail="CLOUD_SQL_INSTANCE not configured")
    return parts[0], parts[2]  # project, instance_name


@router.post("/api/v1/admin/backup")
def create_backup(authorization: str | None = Header(default=None)) -> dict:
    """Trigger an on-demand Cloud SQL backup. Returns the operation ID immediately."""
    _check_token(authorization)
    project, instance = _parse_instance()
    op = _sql_service().backupRuns().insert(project=project, instance=instance).execute()
    logger.info("Backup operation started: %s", op.get("name"))
    return {"operationId": op.get("name"), "status": op.get("status")}


class RestoreRequest(BaseModel):
    backup_id: int


@router.post("/api/v1/admin/restore")
def restore_backup(
    body: RestoreRequest,
    authorization: str | None = Header(default=None),
) -> dict:
    """Restore the database from a Cloud SQL backup by backup ID.
    WARNING: this replaces all current data. Returns the operation ID immediately."""
    _check_token(authorization)
    project, instance = _parse_instance()
    op = (
        _sql_service()
        .instances()
        .restoreBackup(
            project=project,
            instance=instance,
            body={"restoreBackupContext": {"backupRunId": body.backup_id, "project": project}},
        )
        .execute()
    )
    logger.info("Restore operation started: %s", op.get("name"))
    return {"operationId": op.get("name"), "status": op.get("status")}


@router.get("/api/v1/admin/backups")
def list_backups(authorization: str | None = Header(default=None)) -> list[dict]:
    """List available Cloud SQL backups, newest first."""
    _check_token(authorization)
    project, instance = _parse_instance()
    result = _sql_service().backupRuns().list(project=project, instance=instance).execute()
    return [
        {"id": b["id"], "status": b["status"], "startTime": b.get("startTime")}
        for b in result.get("items", [])
    ]


# ---------------------------------------------------------------------------
# Admin panel endpoints (JWT auth — userLevel=3)
# ---------------------------------------------------------------------------


@router.get("/api/v1/admin/competitions")
def admin_get_competitions(db: DbSession, current_user: CurrentUser) -> dict:
    """Get current base and extra competition info."""
    require_admin(db, current_user)
    base = QueryService.get_current_base_competition(db)
    extra = QueryService.get_current_extra_competition(db)
    return {"base": base, "extra": extra}


@router.get("/api/v1/admin/leagues")
def admin_list_leagues(db: DbSession, current_user: CurrentUser) -> list[dict]:
    """List all leagues."""
    require_admin(db, current_user)
    rows = db.execute(
        select(
            League.leagueID,
            League.leagueName,
            League.season,
            League.seasonNum,
            League.commissionerID,
            League.numDivisions,
        ).order_by(League.leagueID.desc())
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/api/v1/admin/leagues/{league_id}/divisions")
def admin_list_divisions(league_id: int, db: DbSession, current_user: CurrentUser) -> list[dict]:
    """List all divisions for a league."""
    require_admin(db, current_user)
    return QueryService.get_divisions_by_league(db, league_id)


@router.get("/api/v1/admin/divisions/{division_id}")
def admin_get_division(division_id: int, db: DbSession, current_user: CurrentUser) -> dict:
    """Get a single division."""
    require_admin(db, current_user)
    division = require_division(db, division_id)
    return QueryService.division_to_dict(division)


class DivisionUpdateRequest(BaseModel):
    draft_type: str | None = None
    draft_date: datetime | None = None
    draft_complete_date: datetime | None = None


@router.put("/api/v1/admin/divisions/{division_id}")
def admin_update_division(
    division_id: int,
    body: DivisionUpdateRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Update draft settings for a division."""
    require_admin(db, current_user)
    division = require_division(db, division_id)

    if body.draft_type is not None:
        division.draftType = body.draft_type
    if body.draft_date is not None:
        division.draftDate = body.draft_date
    if body.draft_complete_date is not None:
        division.draftCompleteDate = body.draft_complete_date

    division.updatedBy = current_user
    division.updatedIn = utc_now()
    db.commit()
    db.refresh(division)

    return {
        "divisionID": division.divisionID,
        "draftType": division.draftType,
        "draftDate": to_iso(division.draftDate),
        "draftCompleteDate": to_iso(division.draftCompleteDate),
        "updatedBy": division.updatedBy,
        "updatedIn": to_iso(division.updatedIn),
    }


@router.post("/api/v1/admin/divisions/{division_id}/shuffle")
def admin_shuffle_teams(division_id: int, db: DbSession, current_user: CurrentUser) -> list[dict]:
    """Randomize draft order for all teams in a division."""
    require_admin(db, current_user)
    require_division(db, division_id)

    teams = db.query(Team).filter(Team.divisionID == division_id).all()
    orders = list(range(1, len(teams) + 1))
    random.shuffle(orders)

    now = utc_now()
    for team, order in zip(teams, orders):
        team.draftOrder = order
        team.updatedIn = now

    db.commit()
    return [{"teamID": t.teamID, "teamName": t.teamName, "draftOrder": t.draftOrder} for t in teams]
