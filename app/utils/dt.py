from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator

_UTC_LOWEST = datetime(2000, 1, 1, tzinfo=timezone.utc).replace(tzinfo=None)
_UTC_LARGEST = datetime.max.replace(tzinfo=timezone.utc).replace(tzinfo=None)

def utc_now() -> datetime:
    """Current UTC time as a naive datetime (DB-safe)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def utc_lowest() -> datetime:
    """Sentinel 'never processed' datetime (2000-01-01 UTC, naive, DB-safe).

    Used as the default for lastF*Date columns so that any real feed date
    compares as newer.
    """
    return _UTC_LOWEST


def utc_largest() -> datetime:
    """Return a largest reasonable UTC datetime (DB-safe)."""
    return _UTC_LARGEST

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
