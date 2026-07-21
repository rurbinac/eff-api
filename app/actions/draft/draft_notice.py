from datetime import datetime
from decimal import Decimal

from app.constants import DraftEvents as Events
from app.services import pusher as pusher_service


class DraftNotice:
    """Batches and sends draft events to clients via Pusher."""

    VALID_EVENTS = {
        Events.DRAFT_START_EVENT,
        Events.DRAFT_PAUSE_EVENT,
        Events.MEMBER_DRAFTED_EVENT,
        Events.DRAFT_MESSAGE_EVENT,
    }

    @staticmethod
    def division_channel(division_id: int) -> str:
        return f"presence-draft-{division_id}"

    def __init__(self, division_id: int):
        self._division_id = division_id
        self._event_name: str | None = None
        self._data: list[dict] = []

    def add_info(self, event_name: str, data: dict) -> bool:
        """Add data to the current batch. Flushes automatically if event type changes."""
        if event_name not in self.VALID_EVENTS:
            return False

        if self._event_name is None:
            self._event_name = event_name
        elif self._event_name != event_name:
            self.send()
            self._event_name = event_name
            self._data = []

        if data:
            self._data.append(_serialize(data))
            return True

        return False

    def send(self) -> None:
        """Send the current batch to Pusher and clear it."""
        payload = self._get_payload()
        if payload is not None:
            pusher_service.trigger(
                self.division_channel(self._division_id),
                self._event_name,
                payload,
            )

    def _get_payload(self) -> dict | list | None:
        if not self._data:
            return None
        return self._data[0] if len(self._data) == 1 else self._data


def _serialize(data: dict) -> dict:
    """Recursively convert non-JSON-serializable values."""
    result = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, Decimal):
            result[key] = float(value)
        elif isinstance(value, dict):
            result[key] = _serialize(value)
        elif isinstance(value, list):
            result[key] = [_serialize(i) if isinstance(i, dict) else i for i in value]
        else:
            result[key] = value
    return result
