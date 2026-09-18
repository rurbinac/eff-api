from fastapi import APIRouter, Form, HTTPException, status

from app.actions.pusher_auth import PusherAuthAction
from app.database import CurrentUser, DbSession

router = APIRouter(tags=["legacy"])


@router.post("/eff/eff_api/PusherAuth.php")
async def pusher_auth(
    db: DbSession,
    user_id: CurrentUser,
    channel_name: str = Form(...),
    socket_id: str = Form(...),
):
    """Pusher presence-channel auth for draft channels.

    Validates that the authenticated user has a team in the requested division,
    then returns a Pusher presence auth token.
    """
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    result = PusherAuthAction.execute(db, user_id, channel_name, socket_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    return result
