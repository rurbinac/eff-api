from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.schemas import SignInRequest, SignUpRequest, UpdateUserRequest
from app.actions.sign import SignInAction, SignOutAction, SignInfoAction, SignUpAction, UpdateUserAction
from app.context import RequestContext

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/debug/original-query")
def debug_original_query(db: Session = Depends(get_db)) -> dict:
    """DEBUG: Execute the original query to see what it returns."""
    RequestContext.set_datetime()
    try:
        # Original query from before the fix
        query = text("""
            SELECT * FROM `MatchDaysStatus`
            WHERE `matchDayMapKey` = '21'
            AND CURRENT_TIMESTAMP >= `startWaivers`
            AND CURRENT_TIMESTAMP < `finishPostMatch`
        """)

        result = db.execute(query).fetchall()

        return {
            "query": "SELECT * FROM MatchDaysStatus WHERE matchDayMapKey='21' AND CURRENT_TIMESTAMP >= startWaivers AND CURRENT_TIMESTAMP < finishPostMatch",
            "matching_records": len(result),
            "records": [
                {
                    "matchDayMapKey": row[3],
                    "realCompetitionMatchDay": row[8],
                    "startWaivers": str(row[27]) if row[27] else None,
                    "finishPostMatch": str(row[41]) if row[41] else None,
                    "scriptsStatus": row[20],
                }
                for row in result
            ] if result else []
        }
    except Exception as e:
        return {
            "error": str(e),
            "query": "SELECT * FROM MatchDaysStatus WHERE matchDayMapKey='21' AND CURRENT_TIMESTAMP >= startWaivers AND CURRENT_TIMESTAMP < finishPostMatch"
        }
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
