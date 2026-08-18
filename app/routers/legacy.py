from fastapi import APIRouter, Form, Query, Request

from app.actions.sign import SignInAction, SignInfoAction, SignOutAction
from app.actions.top_epl import TopEPLAction
from app.context import RequestContext
from app.database import CurrentToken, DbSession

router = APIRouter(tags=["legacy"])


@router.post("/eff/eff_api/Users.php")
async def legacy_users(
    db: DbSession,
    request: Request,
    token: CurrentToken,
    f: str = Query(..., description="Action name"),
    userEmail: str = Form(None),
    userPassword: str = Form(None),
):
    """Legacy PHP-compatible endpoint for Users actions."""
    RequestContext.set_datetime()
    client_ip = request.client.host if request.client else "0.0.0.0"

    try:
        if f == "SignIn":
            session_data = SignInAction.execute(db, userEmail, userPassword, client_ip)
            return {
                "table": "Session",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "values": session_data
            }

        elif f == "SignOut":
            result = SignOutAction.execute(0)
            return {
                "table": "success",
                "values": result,
            }

        elif f == "SignInfo":
            if token is None:
                return {"error": "Missing or invalid token"}
            session_data = SignInfoAction.execute_with_token(db, token)
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
    db: DbSession,
    request: Request,
    userEmail: str = Form(...),
    userPassword: str = Form(...),
):
    """Legacy SignIn endpoint (shortcut)."""
    RequestContext.set_datetime()
    client_ip = request.client.host if request.client else "0.0.0.0"
    session_data = SignInAction.execute(db, userEmail, userPassword, client_ip)
    result = {
        "table": "Session",
        "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
        "values": session_data
    }
    RequestContext.reset()
    return result


@router.post("/eff/eff_api/SignOut.php")
async def legacy_signout():
    """Legacy SignOut endpoint (shortcut)."""
    RequestContext.set_datetime()
    result = SignOutAction.execute(0)
    response = {
        "table": "success",
        "values": result,
    }
    RequestContext.reset()
    return response


@router.post("/eff/eff_api/SignInfo.php")
async def legacy_signinfo(db: DbSession, token: CurrentToken):
    """Legacy SignInfo endpoint (shortcut)."""
    RequestContext.set_datetime()
    if token is None:
        RequestContext.reset()
        return {"error": "Missing or invalid token"}
    session_data = SignInfoAction.execute_with_token(db, token)
    result = {
        "table": "Session",
        "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
        "values": session_data
    }
    RequestContext.reset()
    return result


@router.post("/eff/eff_api/TopEPL.php")
async def legacy_top_epl(db: DbSession):
    """Legacy TopEPL endpoint - returns top 4 EPL teams by standings."""
    RequestContext.set_datetime()
    try:
        return TopEPLAction.execute(db, limit=4)
    finally:
        RequestContext.reset()
