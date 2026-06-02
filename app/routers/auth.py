from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import SignInRequest, SignInResponse, ErrorResponse
from app.actions.sign import SignInAction, SignOutAction, SignInfoAction

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signin", response_model=SignInResponse)
def rest_signin(payload: SignInRequest, http_request: Request, db: Session = Depends(get_db)) -> dict:
    """REST endpoint: Sign in user."""
    # Get client IP
    client_ip = http_request.client.host if http_request.client else "0.0.0.0"
    return SignInAction.execute(db, payload.userEmail, payload.userPassword, client_ip)


@router.post("/signout")
def rest_signout() -> dict:
    """REST endpoint: Sign out user."""
    return SignOutAction.execute(0)
