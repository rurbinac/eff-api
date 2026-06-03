from fastapi import APIRouter, Form, Depends, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.context import RequestContext
from app.actions.sign import SignInfoAction

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
