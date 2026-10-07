from datetime import datetime

from fastapi import APIRouter, Form, Query, Request

from app.actions.sign import ChangePasswordAction, SignInAction, SignUpAction, UpdateUserAction
from app.context import RequestContext
from app.database import CurrentUser, DbSession
from app.exceptions import EFFException, RequiredValueException, UnknownActionException
from app.guards import require_authentication, require_pos_int
from app.schemas import SignUpRequest, UpdateUserRequest
from app.utils.legacy_returns import return_error, return_one_legacy

router = APIRouter(prefix="/api/v1/users", tags=["users"])
legacy_router = APIRouter(tags=["legacy"])


@legacy_router.post("/eff/eff_api/Users.php")
async def legacy_users(
    db: DbSession,
    current_user: CurrentUser,
    request: Request,
    f: str = Query(..., description="Action name"),
    userID: str = Form(None),
    userEmail: str = Form(None),
    userPassword: str = Form(None),
    firstName: str = Form(None),
    lastName: str = Form(None),
    birthday: str = Form(None),
    country: str = Form(None),
    state: str = Form(None),
    city: str = Form(None),
    phoneNumber: str = Form(None),
    timeZone: str = Form(None),
    favoriteTeam: str = Form(None),
):
    """Legacy PHP-compatible endpoint for Users actions."""
    RequestContext.set_datetime()
    try:
        if f == "SignIn":
            session_data = SignInAction.execute(db, userEmail, userPassword, _client_ip(request))
            return return_one_legacy("Session", session_data)
        elif f == "Update":
            require_authentication(current_user)
            require_pos_int(userID, "userID", f)
            parsed_birthday = datetime.fromisoformat(birthday) if birthday else None
            values = UpdateUserAction.execute(
                db=db,
                user_id=int(userID),
                first_name=firstName,
                last_name=lastName,
                birthday=parsed_birthday,
                country=country,
                state=state,
                city=city,
                phone_number=phoneNumber,
                time_zone=timeZone,
                favorite_team=favoriteTeam,
            )
            return return_one_legacy("Users", values)
        elif f == "ChangePassword":
            require_authentication(current_user)
            if not userPassword:
                raise RequiredValueException("userPassword", f)
            values = ChangePasswordAction.execute(db, user_id=current_user, new_password=userPassword)
            return return_one_legacy("Users", values)
        else:
            raise UnknownActionException(f)
    except EFFException as e:
        return return_error(e)
    finally:
        RequestContext.reset()



@router.post("")
def rest_signup(payload: SignUpRequest, db: DbSession) -> dict:
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
    db: DbSession,
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



def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "0.0.0.0"
