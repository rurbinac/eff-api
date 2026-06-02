from fastapi import APIRouter, Depends, Request, Query, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.actions.sign import SignInAction, SignOutAction, SignInfoAction

router = APIRouter(tags=["legacy"])


@router.post("/eff/eff_api/Users.php")
async def legacy_users(
    f: str = Query(..., description="Action name"),
    _type: str | None = Query(None, description="Action type"),
    _format: str | None = Query("json", description="Response format"),
    userEmail: str = Form(None),
    userPassword: str = Form(None),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Legacy PHP-compatible endpoint for Users actions."""

    # Get client IP
    client_ip = request.client.host if request.client else "0.0.0.0"

    if f == "SignIn":
        result = SignInAction.execute(db, userEmail, userPassword, client_ip)
        return {"Session": result, "_format": _format}

    elif f == "SignOut":
        result = SignOutAction.execute(0)
        return {"response": result, "_format": _format}

    elif f == "SignInfo":
        # Parse JWT from header or form data
        # For now, we'll return a placeholder
        return {"error": "Not implemented - need user context"}, 501

    else:
        return {"error": f"Unknown action: {f}"}, 400


@router.post("/eff/eff_api/SignIn.php")
async def legacy_signin(
    userEmail: str = Form(...),
    userPassword: str = Form(...),
    _format: str | None = Query("json"),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Legacy SignIn endpoint (shortcut)."""
    client_ip = request.client.host if request.client else "0.0.0.0"
    result = SignInAction.execute(db, userEmail, userPassword, client_ip)
    return {"Session": result, "_format": _format}


@router.post("/eff/eff_api/SignOut.php")
async def legacy_signout(_format: str | None = Query("json")):
    """Legacy SignOut endpoint (shortcut)."""
    result = SignOutAction.execute(0)
    return {"response": result, "_format": _format}
