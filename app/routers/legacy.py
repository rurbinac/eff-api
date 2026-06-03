from fastapi import APIRouter, Depends, Request, Query, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.actions.sign import SignInAction, SignOutAction, SignInfoAction
from app.context import RequestContext

router = APIRouter(tags=["legacy"])


@router.post("/eff/eff_api/Users.php")
async def legacy_users(
    f: str = Query(..., description="Action name"),
    type: str | None = Query(None, description="Action type", alias="_type"),
    format: str | None = Query("json", description="Response format", alias="_format"),
    userEmail: str = Form(None),
    userPassword: str = Form(None),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible endpoint for Users actions."""
    RequestContext.set_datetime()  # Cache request datetime
    client_ip = request.client.host if request.client else "0.0.0.0"

    try:
        if f == "SignIn":
            result = SignInAction.execute(db, userEmail, userPassword, client_ip)
            return result

        elif f == "SignOut":
            result = SignOutAction.execute(0)
            return {"table": "success", "values": result, "_format": format}

        elif f == "SignInfo":
            # Parse user ID from token or request
            return {"error": "Not implemented - need user context"}, 501

        else:
            return {"error": f"Unknown action: {f}"}, 400
    finally:
        RequestContext.reset()  # Clean up context


@router.post("/eff/eff_api/SignIn.php")
async def legacy_signin(
    userEmail: str = Form(...),
    userPassword: str = Form(...),
    format: str | None = Query("json", alias="_format"),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Legacy SignIn endpoint (shortcut)."""
    RequestContext.set_datetime()  # Cache request datetime
    client_ip = request.client.host if request.client else "0.0.0.0"
    result = SignInAction.execute(db, userEmail, userPassword, client_ip)
    RequestContext.reset()  # Clean up context
    return result


@router.post("/eff/eff_api/SignOut.php")
async def legacy_signout(format: str | None = Query("json", alias="_format")):
    """Legacy SignOut endpoint (shortcut)."""
    result = SignOutAction.execute(0)
    return {"table": "success", "values": result, "_format": format}


@router.post("/eff/eff_api/SignInfo.php")
async def legacy_signinfo(
    format: str | None = Query("json", alias="_format"),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Legacy SignInfo endpoint (shortcut)."""
    # Parse user ID from Authorization header
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return {"error": "Missing or invalid token"}, 401

    token = auth_header[7:]  # Remove "Bearer " prefix
    # For now, just return error - will implement token parsing next
    return {"error": "Token parsing not yet implemented"}, 501
