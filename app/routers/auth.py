from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import SignInRequest
from app.actions.sign import SignInAction, SignOutAction, SignInfoAction
from app.context import RequestContext

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/sign_in")
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


@router.get("/sign_info")
def rest_signinfo(http_request: Request, db: Session = Depends(get_db)) -> dict:
    """REST endpoint: Get current user info from token."""
    RequestContext.set_datetime()
    try:
        # Get token from Authorization header
        auth_header = http_request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return {"error": "Missing or invalid token"}

        token = auth_header[7:]
        # Get data from action
        session_data = SignInfoAction.execute_with_token(db, token)
        # Return as REST object
        return session_data
    finally:
        RequestContext.reset()


@router.post("/sign_out")
def rest_signout() -> dict:
    """REST endpoint: Sign out user."""
    return SignOutAction.execute(0)
