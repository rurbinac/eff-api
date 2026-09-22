import pusher
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User
from app.utils.dt import utc_now

DRAFT_CHANNEL_PREFIX = "presence-draft-"


class PusherAuthAction:
    """Authenticate a Pusher presence channel subscription for draft channels."""

    @staticmethod
    def _draft_division_id(channel_name: str) -> int | None:
        """Return the divisionID from a presence-draft-{divisionID} name, or None if invalid."""
        if not channel_name.startswith(DRAFT_CHANNEL_PREFIX):
            return None
        try:
            div_id = int(channel_name[len(DRAFT_CHANNEL_PREFIX):])
            return div_id if div_id > 0 else None
        except ValueError:
            return None

    @staticmethod
    def execute(db: Session, user_id: int, channel_name: str, socket_id: str) -> dict | None:
        """Validate the subscription request and return a Pusher presence auth token.

        Returns the auth dict on success, or None if the request is forbidden.
        """
        division_id = PusherAuthAction._draft_division_id(channel_name)
        if division_id is None:
            return None

        # User must have a team in this division
        row = db.execute(
            text("""
                SELECT `teamID` FROM `Teams`
                WHERE `divisionID` = :divisionID AND `userID` = :userID
                LIMIT 1
            """),
            {"divisionID": division_id, "userID": user_id},
        ).mappings().first()
        if not row:
            return None

        user = db.get(User, user_id)
        if not user:
            return None

        client = pusher.Pusher(
            app_id=settings.pusher_app_id,
            key=settings.pusher_key,
            secret=settings.pusher_secret,
            cluster=settings.pusher_cluster,
        )

        full_name = f"{user.firstName or ''} {user.lastName or ''}".strip()
        return client.authenticate(
            channel=channel_name,
            socket_id=socket_id,
            custom_data={
                "user_id": str(user_id),
                "user_info": {
                    "userEmail": user.userEmail,
                    "userFullName": full_name,
                    "signInAt": utc_now().strftime("%Y-%m-%d %H:%M:%S"),
                },
            },
        )
