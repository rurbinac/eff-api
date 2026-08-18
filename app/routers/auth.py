from fastapi import APIRouter, Request

from app.actions.sign import SignInAction, SignInfoAction, SignOutAction
from app.context import RequestContext
from app.database import CurrentToken, DbSession
from app.schemas import SignInRequest

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/sign_in")
def rest_signin(payload: SignInRequest, http_request: Request, db: DbSession) -> dict:
    """REST endpoint: Sign in user."""
    RequestContext.set_datetime()
    try:
        client_ip = http_request.client.host if http_request.client else "0.0.0.0"
        return SignInAction.execute(db, payload.userEmail, payload.userPassword, client_ip)
    finally:
        RequestContext.reset()


@router.get("/sign_info")
def rest_signinfo(db: DbSession, token: CurrentToken) -> dict:
    """REST endpoint: Get current user info from token."""
    RequestContext.set_datetime()
    try:
        if token is None:
            return {"error": "Missing or invalid token"}
        return SignInfoAction.execute_with_token(db, token)
    finally:
        RequestContext.reset()


@router.post("/sign_out")
def rest_signout() -> dict:
    """REST endpoint: Sign out user."""
    return SignOutAction.execute(0)
