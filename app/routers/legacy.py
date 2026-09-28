from fastapi import APIRouter, Form, Query, Request

from app.actions.sign import SignInAction, SignInfoAction, SignOutAction
from app.actions.top_epl import TopEPLAction
from app.context import RequestContext
from app.database import CurrentToken, DbSession
from app.exceptions import EFFException, UnknownActionException
from app.utils.legacy_returns import return_error, return_many_legacy, return_one_legacy

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

    try:
        if f == "SignIn":
            session_data = SignInAction.execute(db, userEmail, userPassword, _client_ip(request))
            return return_one_legacy("Session", session_data)

        elif f == "SignOut":
            result = SignOutAction.execute(db, token)
            return return_one_legacy("success", result)

        elif f == "SignInfo":
            if token is None:
                return {"error": "Missing or invalid token"}
            session_data = SignInfoAction.execute_with_token(db, token)
            return return_one_legacy("Session", session_data)

        else:
            raise UnknownActionException(f)
    except EFFException as e:
        return return_error(e)
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
    try:
        session_data = SignInAction.execute(db, userEmail, userPassword, _client_ip(request))
        return return_one_legacy("Session", session_data)
    finally:
        RequestContext.reset()


@router.post("/eff/eff_api/SignOut.php")
async def legacy_signout(db: DbSession, token: CurrentToken):
    """Legacy SignOut endpoint (shortcut)."""
    RequestContext.set_datetime()
    try:
        result = SignOutAction.execute(db, token)
        return return_one_legacy("success", result)
    finally:
        RequestContext.reset()


@router.post("/eff/eff_api/SignInfo.php")
async def legacy_signinfo(db: DbSession, token: CurrentToken):
    """Legacy SignInfo endpoint (shortcut)."""
    RequestContext.set_datetime()
    try:
        if token is None:
            return {"error": "Missing or invalid token"}
        session_data = SignInfoAction.execute_with_token(db, token)
        return return_one_legacy("Session", session_data)
    finally:
        RequestContext.reset()


@router.post("/eff/eff_api/TopEPL.php")
async def legacy_top_epl(db: DbSession):
    """Legacy TopEPL endpoint - returns top 4 EPL teams by standings."""
    RequestContext.set_datetime()
    try:
        items = TopEPLAction.execute(db, limit=4)
        return return_many_legacy("TopEPL", items)
    finally:
        RequestContext.reset()

def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "0.0.0.0"
