from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator


def utc_now() -> datetime:
    """Current UTC time as a naive datetime (DB-safe)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class UTCDateTime(TypeDecorator):
    """
    Stores datetimes as naive UTC in MySQL DATETIME columns.

    On write: aware datetimes are converted to UTC then stripped; naive
    datetimes pass through unchanged (assumed to already be UTC).
    On read: value comes back naive from MySQL — caller must treat it as UTC.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        return value
