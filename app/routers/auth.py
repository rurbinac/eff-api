from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import SignInRequest, SignUpRequest
from app.actions.sign import SignInAction, SignOutAction, SignInfoAction, SignUpAction, UpdateUserAction
from app.context import RequestContext

router = APIRouter(prefix="/api/auth", tags=["auth"])


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
    payload: SignUpRequest,
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
