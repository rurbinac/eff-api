from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import SignUpRequest, UpdateUserRequest
from app.actions.sign import SignUpAction, UpdateUserAction
from app.context import RequestContext

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("")
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


@router.patch("/{user_id}")
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
