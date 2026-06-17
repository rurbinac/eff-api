from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.schemas import SignInRequest, SignUpRequest, UpdateUserRequest
from app.actions.sign import SignInAction, SignOutAction, SignInfoAction, SignUpAction, UpdateUserAction
from app.context import RequestContext

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/debug/query-comparison")
def debug_query_comparison(db: Session = Depends(get_db)) -> dict:
    """DEBUG: Compare original vs fixed query for match day 35."""
    RequestContext.set_datetime()
    try:
        # Original query
        original_query = text("""
            SELECT matchDayMapKey, realCompetitionMatchDay, startWaivers, finishPostMatch, scriptsStatus
            FROM `MatchDaysStatus`
            WHERE `matchDayMapKey` = '21' AND realCompetitionMatchDay = 35
            AND CURRENT_TIMESTAMP >= `startWaivers`
            AND CURRENT_TIMESTAMP < `finishPostMatch`
        """)

        # Fixed query
        fixed_query = text("""
            SELECT matchDayMapKey, realCompetitionMatchDay, startMatchDay, finishMatchDay, scriptsStatus
            FROM `MatchDaysStatus`
            WHERE `matchDayMapKey` = '21' AND realCompetitionMatchDay = 35
            AND CURRENT_TIMESTAMP >= `startMatchDay`
            AND CURRENT_TIMESTAMP < `finishMatchDay`
        """)

        # Get the full record to show all date fields
        full_record = text("""
            SELECT matchDayMapKey, realCompetitionMatchDay,
                   startWaivers, finishPostMatch,
                   startMatchDay, finishMatchDay,
                   scriptsStatus
            FROM `MatchDaysStatus`
            WHERE `matchDayMapKey` = '21' AND realCompetitionMatchDay = 35
        """)

        original_result = db.execute(original_query).fetchone()
        fixed_result = db.execute(fixed_query).fetchone()
        full_data = db.execute(full_record).fetchone()

        return {
            "match_day": 35,
            "database_dates": {
                "startWaivers": str(full_data[2]) if full_data and full_data[2] else None,
                "finishPostMatch": str(full_data[3]) if full_data and full_data[3] else None,
                "startMatchDay": str(full_data[4]) if full_data and full_data[4] else None,
                "finishMatchDay": str(full_data[5]) if full_data and full_data[5] else None,
                "scriptsStatus": full_data[6] if full_data else None,
            },
            "original_query_result": "MATCHES" if original_result else "NO MATCH",
            "fixed_query_result": "MATCHES" if fixed_result else "NO MATCH",
            "note": "Original query uses waivers period, fixed query uses match day period"
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        RequestContext.reset()


@router.post("/signin")
def rest_signin(payload: SignInRequest, http_request: Request, db: Session = Depends(get_db)) -> dict:
    """REST endpoint: Sign in user."""
    RequestContext.set_datetime()
    try:
        # Get client IP
        client_ip = http_request.client.host if http_request.client else "0.0.0.0"
        # Get data from action
        session_data = SignInAction.execute(db, payload.userEmail, payload.userPassword, client_ip)
        # Return as REST array
        return session_data
    finally:
        RequestContext.reset()


@router.post("/signout")
def rest_signout() -> dict:
    """REST endpoint: Sign out user."""
    return SignOutAction.execute(0)


@router.post("/signup")
def rest_signup(payload: SignUpRequest, db: Session = Depends(get_db)) -> dict:
    """REST endpoint: Create new user account."""
    RequestContext.set_datetime()
    try:
        # Get data from action
        session_data = SignUpAction.execute(
            db=db,
            user_email=payload.userEmail,
            user_password=payload.userPassword,
            user_name=payload.userName,
            first_name=payload.firstName,
            last_name=payload.lastName,
            birthday=payload.birthday,
            country=payload.country,
            state=payload.state,
            city=payload.city,
            phone_number=payload.phoneNumber,
            time_zone=payload.timeZone,
            favorite_team=payload.favoriteTeam,
        )
        # Return as REST object
        return session_data
    finally:
        RequestContext.reset()


@router.patch("/users/{user_id}")
def rest_update_user(
    user_id: int,
    payload: UpdateUserRequest,
    db: Session = Depends(get_db),
) -> dict:
    """REST endpoint: Update user profile."""
    RequestContext.set_datetime()
    try:
        # Get data from action
        session_data = UpdateUserAction.execute(
            db=db,
            user_id=user_id,
            first_name=payload.firstName,
            last_name=payload.lastName,
            birthday=payload.birthday,
            country=payload.country,
            state=payload.state,
            city=payload.city,
            phone_number=payload.phoneNumber,
            time_zone=payload.timeZone,
            favorite_team=payload.favoriteTeam,
        )
        # Return as REST object
        return session_data
    finally:
        RequestContext.reset()
