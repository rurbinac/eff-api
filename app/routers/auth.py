from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import SignInRequest, SignInResponse, ErrorResponse
from app.actions.sign import SignInAction, SignOutAction, SignInfoAction
from app.context import RequestContext

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signin")
def rest_signin(payload: SignInRequest, http_request: Request, db: Session = Depends(get_db)) -> dict:
    """REST endpoint: Sign in user."""
    RequestContext.set_datetime()  # Cache request datetime
    # Get client IP
    client_ip = http_request.client.host if http_request.client else "0.0.0.0"
    result = SignInAction.execute(db, payload.userEmail, payload.userPassword, client_ip)
    RequestContext.reset()  # Clean up context
    return result


@router.post("/signout")
def rest_signout() -> dict:
    """REST endpoint: Sign out user."""
    return SignOutAction.execute(0)
