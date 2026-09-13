from datetime import datetime, timedelta, timezone

from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator

_UTC_LOWEST = datetime(1000, 1, 1, tzinfo=timezone.utc).replace(tzinfo=None)  # MySQL DATETIME min
_UTC_LARGEST = datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc).replace(tzinfo=None)  # MySQL DATETIME max


def utc_now(microsecond: bool = False) -> datetime:
    """Current UTC time as a naive datetime (DB-safe).

    Args:
        microsecond: If True, keeps microsecond precision (for DATETIME(6) columns).
                     If False (default), truncates to seconds (for plain DATETIME columns).
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return now if microsecond else now.replace(microsecond=0)


def utc_lowest() -> datetime:
    """Sentinel minimum datetime (1000-01-01 UTC, naive, DB-safe — MySQL DATETIME min).

    Used as the open-ended lower bound so that any real date compares as newer.
    """
    return _UTC_LOWEST


def utc_largest() -> datetime:
    """Return a largest reasonable UTC datetime (DB-safe)."""
    return _UTC_LARGEST


def add_minutes(dt: datetime, minutes: int) -> datetime:
    """Return dt shifted by the given number of minutes (negative to go back)."""
    return dt + timedelta(minutes=minutes)


def add_hours(dt: datetime, hours: int) -> datetime:
    """Return dt shifted by the given number of hours (negative to go back)."""
    return dt + timedelta(hours=hours)


def add_days(dt: datetime, days: int) -> datetime:
    """Return dt shifted by the given number of days (negative to go back)."""
    return dt + timedelta(days=days)


def next_midnight(dt: datetime) -> datetime:
    """Return 00:00:00 of the day after dt (always moves forward at least one day)."""
    return (dt + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)


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
