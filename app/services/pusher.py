import logging
import os

import pusher

logger = logging.getLogger(__name__)

_client: pusher.Pusher | None = None


def get_client() -> pusher.Pusher:
    global _client
    if _client is None:
        _client = pusher.Pusher(
            app_id=os.environ["PUSHER_APP_ID"],
            key=os.environ["PUSHER_KEY"],
            secret=os.environ["PUSHER_SECRET"],
            cluster="mt1",
            ssl=True,
            timeout=5,
        )
    return _client


def trigger(channel: str, event: str, data: dict) -> None:
    try:
        get_client().trigger(channel, event, data)
    except Exception as e:
        logger.warning("Pusher trigger failed: %s", e)
