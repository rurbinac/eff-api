from fastapi import APIRouter, Form, Depends, Header, Request
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.context import RequestContext
from app.actions.sign import SignInfoAction, SignOutAction, SignUpAction, UpdateUserAction
from app.security import decode_token

router = APIRouter()


@router.post("/gaming/api/SignInfo.php")
async def gaming_api_sign_info(
    format: str = Form("json", alias="_format"),
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    """Gaming API SignInfo endpoint - token-based authentication."""
    RequestContext.set_datetime()
    try:
        # Extract token from Authorization header (Bearer token)
        token = None
        if authorization:
            if authorization.startswith("Bearer "):
                token = authorization[7:]
            else:
                token = authorization

        if not token:
            return {"error": "Missing authentication token"}

        # Verify token and return user info with context
        return SignInfoAction.execute_with_token(db, token)

    finally:
        RequestContext.reset()


@router.post("/gaming/api/SignOut.php")
async def gaming_api_sign_out(
    format: str = Form("json", alias="_format"),
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    """Gaming API SignOut endpoint - token-based logout."""
    RequestContext.set_datetime()
    try:
        # Extract token from Authorization header
        token = None
        if authorization:
            if authorization.startswith("Bearer "):
                token = authorization[7:]
            else:
                token = authorization

        if not token:
            return {"error": "Missing authentication token"}

        # Verify token is valid (just to confirm user is authenticated)
        payload = decode_token(token)
        if not payload:
            return {"error": "Invalid or expired token"}

        # Return success (token invalidation happens on client side)
        return SignOutAction.execute(0)

    finally:
        RequestContext.reset()


@router.post("/gaming/api/Users.php")
async def gaming_api_users(
    f: str = None,
    format: str = Form("json", alias="_format"),
    userID: int = Form(None),
    firstName: str = Form(None),
    lastName: str = Form(None),
    birthday: str = Form(default=None),
    country: str = Form(default=None),
    state: str = Form(default=None),
    city: str = Form(default=None),
    phoneNumber: str = Form(default=None),
    timeZone: str = Form(default=None),
    favoriteTeam: str = Form(default=None),
    authorization: str = Header(None),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Gaming API Users endpoint - update user profile."""
    RequestContext.set_datetime()
    try:
        if f != "Update":
            return {"error": f"Unknown function: {f}"}

        # If userID not provided, try to get from token
        if not userID:
            token = None
            if authorization:
                if authorization.startswith("Bearer "):
                    token = authorization[7:]
                else:
                    token = authorization

            if not token:
                return {"error": "Missing userID or authentication token"}

            payload = decode_token(token)
            if not payload:
                return {"error": "Invalid or expired token"}

            userID = int(payload.get("sub"))

        # Parse birthday if provided
        birthday_dt = None
        if birthday:
            try:
                birthday_dt = datetime.fromisoformat(birthday)
            except ValueError:
                return {"error": "Invalid birthday format, use YYYY-MM-DD"}

        # Update user
        return UpdateUserAction.execute(
            db=db,
            user_id=userID,
            first_name=firstName,
            last_name=lastName,
            birthday=birthday_dt,
            country=country,
            state=state,
            city=city,
            phone_number=phoneNumber,
            time_zone=timeZone,
            favorite_team=favoriteTeam,
        )

    except Exception as e:
        return {"error": str(e)}

    finally:
        RequestContext.reset()


@router.post("/gaming/api/SignUp.php")
async def gaming_api_sign_up(
    format: str = Form("json", alias="_format"),
    userEmail: str = Form(...),
    userPassword: str = Form(...),
    userName: str = Form(default=""),
    firstName: str = Form(...),
    lastName: str = Form(...),
    birthday: str = Form(default=None),
    country: str = Form(default=None),
    state: str = Form(default=None),
    city: str = Form(default=None),
    phoneNumber: str = Form(default=None),
    timeZone: str = Form(default=None),
    favoriteTeam: str = Form(default=None),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Gaming API SignUp endpoint - create new user account."""
    RequestContext.set_datetime()
    try:
        # Parse birthday if provided
        birthday_dt = None
        if birthday:
            try:
                birthday_dt = datetime.fromisoformat(birthday)
            except ValueError:
                return {"error": "Invalid birthday format, use YYYY-MM-DD"}

        # Get client IP
        client_ip = request.client.host if request.client else "0.0.0.0"

        # Create user and return session
        return SignUpAction.execute(
            db=db,
            user_email=userEmail,
            user_password=userPassword,
            user_name=userName,
            first_name=firstName,
            last_name=lastName,
            birthday=birthday_dt,
            country=country if country else None,
            state=state if state else None,
            city=city if city else None,
            phone_number=phoneNumber if phoneNumber else None,
            time_zone=timeZone if timeZone else None,
            favorite_team=favoriteTeam if favoriteTeam else None,
        )

    except Exception as e:
        return {"error": str(e)}

    finally:
        RequestContext.reset()
