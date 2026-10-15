import logging
import random
from datetime import datetime

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, text

from app.config import settings
from app.database import CurrentUser, DbSession
from app.guards import require_admin, require_division
from app.models import Division, League, MatchDaysMap, MatchDaysStatus, Process, RealCompetition, RealStanding, RealTeamMember, Team, User
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


@router.get("/api/v1/admin/users")
def admin_list_users(db: DbSession, current_user: CurrentUser) -> list[dict]:
    """List all users."""
    require_admin(db, current_user)
    rows = db.execute(
        select(
            User.userID,
            User.userEmail,
            User.userName,
            User.firstName,
            User.lastName,
            User.userLevel,
            User.lastSignInDate,
            User.lastSignInIP,
            User.createdIn,
        ).order_by(User.userID)
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/api/v1/admin/users/{user_id}")
def admin_get_user(user_id: int, db: DbSession, current_user: CurrentUser) -> dict:
    """Get full detail for a single user (no password)."""
    require_admin(db, current_user)
    row = db.execute(
        select(
            User.userID,
            User.userEmail,
            User.userName,
            User.firstName,
            User.lastName,
            User.userLevel,
            User.birthday,
            User.country,
            User.state,
            User.city,
            User.phoneNumber,
            User.timeZone,
            User.favoriteTeam,
            User.lastSignInDate,
            User.lastSignInIP,
            User.createdIn,
            User.updatedIn,
        ).where(User.userID == user_id)
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(row)


@router.get("/api/v1/admin/match-day-statuses/seasons")
def admin_mds_seasons(db: DbSession, current_user: CurrentUser) -> list[str]:
    """Distinct season IDs in MatchDaysStatus, newest first."""
    require_admin(db, current_user)
    rows = db.execute(
        select(MatchDaysStatus.realCompetitionSeasonId)
        .distinct()
        .order_by(MatchDaysStatus.realCompetitionSeasonId.desc())
    ).scalars().all()
    return list(rows)


@router.get("/api/v1/admin/match-day-statuses/map-keys")
def admin_mds_map_keys(
    db: DbSession,
    current_user: CurrentUser,
    season_id: str | None = None,
) -> list[str]:
    """Distinct matchDayMapKey values for a season."""
    require_admin(db, current_user)
    q = (
        select(MatchDaysStatus.matchDayMapKey)
        .distinct()
        .where(MatchDaysStatus.matchDayMapKey.isnot(None))
    )
    if season_id:
        q = q.where(MatchDaysStatus.realCompetitionSeasonId == season_id)
    rows = db.execute(q.order_by(MatchDaysStatus.matchDayMapKey)).scalars().all()
    return list(rows)


@router.get("/api/v1/admin/match-day-statuses")
def admin_list_mds(
    db: DbSession,
    current_user: CurrentUser,
    season_id: str | None = None,
    match_day_map_key: str | None = None,
) -> list[dict]:
    """List MatchDaysStatus records filtered by season and optional map key."""
    require_admin(db, current_user)
    if season_id is None:
        season_id = str(QueryService.get_season_id())
    q = (
        select(
            MatchDaysStatus.matchDayStatusID,
            MatchDaysStatus.matchDayMapKey,
            MatchDaysStatus.realCompetitionSYMID,
            MatchDaysStatus.realCompetitionMatchDay,
            MatchDaysStatus.prevActiveRealCompetitionSYMID,
            MatchDaysStatus.prevActiveRealCompetitionMatchDay,
            MatchDaysStatus.nextActiveRealCompetitionSYMID,
            MatchDaysStatus.nextActiveRealCompetitionMatchDay,
            MatchDaysStatus.active,
            MatchDaysStatus.overlapped,
            MatchDaysStatus.locked,
            MatchDaysStatus.scriptsStatus,
            MatchDaysStatus.minRealMatchDate,
            MatchDaysStatus.maxRealMatchDate,
            MatchDaysStatus.startWaivers,
            MatchDaysStatus.finishWaivers,
            MatchDaysStatus.startWaiversSettle,
            MatchDaysStatus.finishWaiversSettle,
            MatchDaysStatus.startOpenWaivers,
            MatchDaysStatus.finishOpenWaivers,
            MatchDaysStatus.startOpenWaiversSettle,
            MatchDaysStatus.finishOpenWaiversSettle,
            MatchDaysStatus.startPreMatch,
            MatchDaysStatus.finishPreMatch,
            MatchDaysStatus.startMatch,
            MatchDaysStatus.finishMatch,
            MatchDaysStatus.startPostMatch,
            MatchDaysStatus.finishPostMatch,
            MatchDaysStatus.finishMatchDay,
            MatchDaysStatus.finishBaseMatchDay,
            MatchDaysStatus.minAllowedRealMatchDate,
            MatchDaysStatus.maxAllowedRealMatchDate,
        )
        .where(MatchDaysStatus.realCompetitionSeasonId == season_id)
        .order_by(MatchDaysStatus.realCompetitionMatchDay, MatchDaysStatus.realCompetitionMatchDaySort)
    )
    if match_day_map_key:
        q = q.where(MatchDaysStatus.matchDayMapKey == match_day_map_key)
    rows = db.execute(q).mappings().all()
    return [dict(r) for r in rows]


@router.get("/api/v1/admin/competitions")
def admin_get_competitions(db: DbSession, current_user: CurrentUser) -> dict:
    """Get current base and extra competition info."""
    require_admin(db, current_user)
    base = QueryService.get_current_base_competition(db)
    extra = QueryService.get_current_extra_competition(db)
    return {"base": base, "extra": extra}


@router.get("/api/v1/admin/leagues")
def admin_list_leagues(
    db: DbSession,
    current_user: CurrentUser,
    user_id: int | None = None,
) -> list[dict]:
    """List leagues, optionally filtered to those where a user has a team."""
    require_admin(db, current_user)
    q = select(
        League.leagueID,
        League.leagueName,
        League.season,
        League.seasonNum,
        League.commissionerID,
        League.numDivisions,
    ).order_by(League.leagueID.desc())
    if user_id is not None:
        user_league_ids = (
            select(Division.leagueID)
            .join(Team, Team.divisionID == Division.divisionID)
            .where(Team.userID == user_id)
            .distinct()
            .scalar_subquery()
        )
        q = q.where(League.leagueID.in_(user_league_ids))
    rows = db.execute(q).mappings().all()
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


# ---------------------------------------------------------------------------
# Match Days Map endpoints (JWT auth — userLevel=3)
# ---------------------------------------------------------------------------


@router.get("/api/v1/admin/match-days-map/groups")
def admin_mdm_groups(db: DbSession, current_user: CurrentUser) -> list[dict]:
    """Distinct groups (SYMID, season, firstMatchDay) for the dropdown."""
    require_admin(db, current_user)
    rows = db.execute(
        select(
            MatchDaysMap.realCompetitionSYMID,
            MatchDaysMap.realCompetitionSeasonId,
            MatchDaysMap.firstRealCompetitionMatchDay,
        )
        .distinct()
        .order_by(
            MatchDaysMap.realCompetitionSeasonId.desc(),
            MatchDaysMap.realCompetitionSYMID,
            MatchDaysMap.firstRealCompetitionMatchDay,
        )
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/api/v1/admin/match-days-map")
def admin_list_mdm(
    db: DbSession,
    current_user: CurrentUser,
    symid: str | None = None,
    season_id: str | None = None,
    first_md: int | None = None,
) -> list[dict]:
    """List MatchDaysMap rows filtered by competition, season and first match day."""
    require_admin(db, current_user)
    q = (
        select(
            MatchDaysMap.matchDayMapID,
            MatchDaysMap.competitionType,
            MatchDaysMap.minNumTeams,
            MatchDaysMap.maxNumTeams,
            MatchDaysMap.rounds,
            MatchDaysMap.totalMatchDays,
            MatchDaysMap.matchDay,
            MatchDaysMap.realCompetitionSYMID,
            MatchDaysMap.realCompetitionSeasonId,
            MatchDaysMap.realCompetitionMatchDay,
            MatchDaysMap.firstRealCompetitionMatchDay,
        )
        .order_by(
            MatchDaysMap.minNumTeams,
            MatchDaysMap.maxNumTeams,
            MatchDaysMap.matchDay,
        )
    )
    if symid:
        q = q.where(MatchDaysMap.realCompetitionSYMID == symid)
    if season_id:
        q = q.where(MatchDaysMap.realCompetitionSeasonId == season_id)
    if first_md is not None:
        q = q.where(MatchDaysMap.firstRealCompetitionMatchDay == first_md)
    rows = db.execute(q).mappings().all()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Real Competitions (JWT auth)
# ---------------------------------------------------------------------------


@router.get("/api/v1/admin/real-competitions")
def admin_list_real_competitions(db: DbSession, current_user: CurrentUser) -> list[dict]:
    """List all real competitions ordered by season desc, then ID."""
    require_admin(db, current_user)
    rows = db.execute(
        select(
            RealCompetition.realCompetitionID,
            RealCompetition.realCompetitionUID,
            RealCompetition.realCompetitionSYMID,
            RealCompetition.realCompetitionName,
            RealCompetition.realCompetitionCountry,
            RealCompetition.realCompetitionSeasonId,
            RealCompetition.realCompetitionSeasonName,
            RealCompetition.realCompetitionLastMatchDay,
            RealCompetition.baseRealCompetitionID,
            RealCompetition.extraRealCompetitionID,
        ).order_by(
            RealCompetition.realCompetitionSeasonId.desc(),
            RealCompetition.realCompetitionID,
        )
    ).mappings().all()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Real Matches (JWT auth)
# ---------------------------------------------------------------------------


@router.get("/api/v1/admin/real-matches")
def admin_list_real_matches(
    db: DbSession,
    current_user: CurrentUser,
    symid: str | None = None,
    season_id: str | None = None,
) -> list[dict]:
    """List real matches for a competition/season, joining team rows."""
    require_admin(db, current_user)
    if not symid or not season_id:
        return []
    q = text("""
        SELECT
            m.realMatchID,
            m.realCompetitionSYMID,
            m.realCompetitionMatchDay,
            m.realMatchDate,
            m.realMatchPeriod,
            m.realMatchAttendance,
            t1.realTeamSide        AS firstSide,
            t1.realTeamName        AS firstName,
            t1.realTeamShortName   AS firstShortName,
            t1.realTeamScore       AS firstScore,
            t2.realTeamSide        AS secondSide,
            t2.realTeamName        AS secondName,
            t2.realTeamShortName   AS secondShortName,
            t2.realTeamScore       AS secondScore
        FROM RealMatches m
        JOIN RealMatchTeams t1 ON t1.realMatchID = m.realMatchID AND t1.realTeamNumber = 1
        JOIN RealMatchTeams t2 ON t2.realMatchID = m.realMatchID AND t2.realTeamNumber = 2
        WHERE m.realCompetitionSYMID = :symid
          AND m.realCompetitionSeasonId = :season_id
        ORDER BY m.realMatchDate, m.realMatchID
    """)
    rows = db.execute(q, {"symid": symid, "season_id": season_id}).mappings().all()
    result = []
    for r in rows:
        row = dict(r)
        row["realMatchDate"] = to_iso(row["realMatchDate"])
        result.append(row)
    return result


# ---------------------------------------------------------------------------
# Real Team Members (JWT auth)
# ---------------------------------------------------------------------------


@router.get("/api/v1/admin/real-team-members/seasons")
def admin_rtm_seasons(db: DbSession, current_user: CurrentUser) -> list[str]:
    """Distinct seasons that have RealTeamMember rows, newest first."""
    require_admin(db, current_user)
    rows = db.execute(
        select(RealCompetition.realCompetitionSeasonId)
        .distinct()
        .where(
            RealCompetition.realCompetitionID.in_(
                select(RealTeamMember.baseRealCompetitionID).distinct()
            )
        )
        .order_by(RealCompetition.realCompetitionSeasonId.desc())
    ).scalars().all()
    return list(rows)


@router.get("/api/v1/admin/real-team-members")
def admin_list_real_team_members(
    db: DbSession,
    current_user: CurrentUser,
    season_id: str | None = None,
) -> list[dict]:
    """List RealTeamMembers for a season, joined to RealCompetition for the season filter."""
    require_admin(db, current_user)
    if not season_id:
        return []
    q = text("""
        SELECT
            rtm.realTeamMemberKey  AS `key`,
            rtm.name,
            rtm.position,
            rtm.realTeamName       AS teamName,
            rtm.realTeamShortName  AS teamShortName
        FROM RealTeamMembers rtm
        JOIN RealCompetitions rc ON rc.realCompetitionID = rtm.baseRealCompetitionID
        WHERE rc.realCompetitionSeasonId = :season_id
        ORDER BY rtm.sortName
    """)
    rows = db.execute(q, {"season_id": season_id}).mappings().all()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Real Standings (JWT auth)
# ---------------------------------------------------------------------------


@router.get("/api/v1/admin/real-standings/seasons")
def admin_rs_seasons(db: DbSession, current_user: CurrentUser) -> list[str]:
    """Distinct seasons in RealStandings, newest first."""
    require_admin(db, current_user)
    rows = db.execute(
        select(RealStanding.realCompetitionSeasonId)
        .distinct()
        .order_by(RealStanding.realCompetitionSeasonId.desc())
    ).scalars().all()
    return list(rows)


@router.get("/api/v1/admin/real-standings/match-days")
def admin_rs_match_days(
    db: DbSession,
    current_user: CurrentUser,
    season_id: str | None = None,
) -> list[int]:
    """Distinct match days for a season in RealStandings, ascending."""
    require_admin(db, current_user)
    q = select(RealStanding.realCompetitionMatchDay).distinct()
    if season_id:
        q = q.where(RealStanding.realCompetitionSeasonId == season_id)
    rows = db.execute(q.order_by(RealStanding.realCompetitionMatchDay)).scalars().all()
    return list(rows)


@router.get("/api/v1/admin/real-standings")
def admin_list_real_standings(
    db: DbSession,
    current_user: CurrentUser,
    season_id: str | None = None,
    match_day: int | None = None,
) -> list[dict]:
    """List RealStandings for a season and match day."""
    require_admin(db, current_user)
    if not season_id or match_day is None:
        return []
    rows = db.execute(
        select(
            RealStanding.realTeamMemberKey,
            RealStanding.name,
            RealStanding.position,
            RealStanding.realTeamName,
            RealStanding.realTeamShortName,
        )
        .where(RealStanding.realCompetitionSeasonId == season_id)
        .where(RealStanding.realCompetitionMatchDay == match_day)
        .order_by(RealStanding.sortName)
    ).mappings().all()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Backup / restore — JWT auth (admin panel UI)
# ---------------------------------------------------------------------------


@router.get("/api/v1/admin/backup-runs")
def admin_list_backup_runs(db: DbSession, current_user: CurrentUser) -> list[dict]:
    """List Cloud SQL backup runs."""
    require_admin(db, current_user)
    project, instance = _parse_instance()
    result = _sql_service().backupRuns().list(project=project, instance=instance).execute()
    return [
        {"id": b["id"], "status": b["status"], "startTime": b.get("startTime"), "endTime": b.get("endTime")}
        for b in result.get("items", [])
    ]


@router.post("/api/v1/admin/backup-runs")
def admin_create_backup_run(db: DbSession, current_user: CurrentUser) -> dict:
    """Trigger a new Cloud SQL backup."""
    require_admin(db, current_user)
    project, instance = _parse_instance()
    op = _sql_service().backupRuns().insert(project=project, instance=instance).execute()
    logger.info("Backup started by user %s: %s", current_user, op.get("name"))
    return {"operationId": op.get("name"), "status": op.get("status")}


class RestoreRunRequest(BaseModel):
    backup_id: int


@router.post("/api/v1/admin/backup-runs/restore")
def admin_restore_backup_run(
    body: RestoreRunRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Restore from a Cloud SQL backup. WARNING: replaces all current data."""
    require_admin(db, current_user)
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
    logger.info("Restore of backup %s started by user %s: %s", body.backup_id, current_user, op.get("name"))
    return {"operationId": op.get("name"), "status": op.get("status")}


@router.get("/api/v1/admin/processes")
def admin_list_processes(db: DbSession, current_user: CurrentUser, process_type: str | None = None):
    require_admin(db, current_user)
    q = select(Process).order_by(Process.startDate.desc()).limit(500)
    if process_type:
        q = q.where(Process.processType == process_type)
    rows = db.execute(q).scalars().all()
    result = []
    for r in rows:
        result.append({
            "processID": r.processID,
            "prevProcessID": r.prevProcessID,
            "processType": r.processType,
            "processName": r.processName,
            "startDate": to_iso(r.startDate, timespec="microseconds"),
            "finishDate": to_iso(r.finishDate, timespec="microseconds") if r.finishDate else None,
            "duration": r.duration,
            "versions": r.versions,
            "tasks": r.tasks,
        })
    return result


@router.get("/api/v1/admin/processes/types")
def admin_list_process_types(db: DbSession, current_user: CurrentUser):
    require_admin(db, current_user)
    rows = db.execute(select(Process.processType).distinct()).scalars().all()
    return sorted(rows)
