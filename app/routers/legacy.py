from fastapi import APIRouter, Depends, Request, Query, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.actions.sign import SignInAction, SignOutAction, SignInfoAction
from app.context import RequestContext
from app.security import decode_token

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
    RequestContext.set_datetime()
    client_ip = request.client.host if request.client else "0.0.0.0"

    try:
        if f == "SignIn":
            # Get data from action
            session_data = SignInAction.execute(db, userEmail, userPassword, client_ip)
            # Format as legacy PHP response
            return {
                "table": "Session",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "values": session_data
            }

        elif f == "SignOut":
            # Get data from action
            result = SignOutAction.execute(0)
            # Format as legacy PHP response
            return {
                "table": "success",
                "values": result,
            }

        elif f == "SignInfo":
            # Get token from Authorization header
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return {"error": "Missing or invalid token"}

            token = auth_header[7:]
            # Get data from action
            session_data = SignInfoAction.execute_with_token(db, token)
            # Format as legacy PHP response
            return {
                "table": "Session",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "values": session_data
            }

        else:
            return {"error": f"Unknown action: {f}"}
    finally:
        RequestContext.reset()


@router.post("/eff/eff_api/SignIn.php")
async def legacy_signin(
    userEmail: str = Form(...),
    userPassword: str = Form(...),
    format: str | None = Query("json", alias="_format"),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Legacy SignIn endpoint (shortcut)."""
    RequestContext.set_datetime()
    client_ip = request.client.host if request.client else "0.0.0.0"
    # Get data from action
    session_data = SignInAction.execute(db, userEmail, userPassword, client_ip)
    # Format as legacy PHP response
    result = {
        "table": "Session",
        "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
        "values": session_data
    }
    RequestContext.reset()
    return result


@router.post("/eff/eff_api/SignOut.php")
async def legacy_signout(format: str | None = Query("json", alias="_format")):
    """Legacy SignOut endpoint (shortcut)."""
    RequestContext.set_datetime()
    # Get data from action
    result = SignOutAction.execute(0)
    # Format as legacy PHP response
    response = {
        "table": "success",
        "values": result,
    }
    RequestContext.reset()
    return response


@router.post("/eff/eff_api/SignInfo.php")
async def legacy_signinfo(
    format: str | None = Query("json", alias="_format"),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Legacy SignInfo endpoint (shortcut)."""
    RequestContext.set_datetime()
    # Get token from Authorization header
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        RequestContext.reset()
        return {"error": "Missing or invalid token"}

    token = auth_header[7:]
    # Get data from action
    session_data = SignInfoAction.execute_with_token(db, token)
    # Format as legacy PHP response
    result = {
        "table": "Session",
        "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
        "values": session_data
    }
    RequestContext.reset()
    return result
