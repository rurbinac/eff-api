from datetime import date, datetime, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo

from dateutil import parser as _dateutil_parser
from dateutil.parser import ParserError
from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator

_UTC_LOWEST = datetime(1000, 1, 1, tzinfo=timezone.utc).replace(
    tzinfo=None
)  # MySQL DATETIME min
_UTC_LARGEST = datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc).replace(
    tzinfo=None
)  # MySQL DATETIME max


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




def to_tz(dt: datetime, tz: tzinfo | str | None = timezone.utc) -> datetime:
    """Convert dt to the given timezone.

    - Aware datetimes: converted to tz (instant preserved, e.g. values from UTCDateTime columns).
    - Naive datetimes: tz is *attached* without shifting the time value.
    - tz=None: tzinfo is stripped; the instant is NOT converted first.
    - tz accepts a tzinfo object or an IANA name string(e.g. 'Europe/London').
    """
    if isinstance(tz, str):
        tz = ZoneInfo(tz) if tz.strip() else None

    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        return dt.replace(tzinfo=tz)
    if tz is None:
        return dt.replace(tzinfo=None)
    return dt.astimezone(tz)


def to_datetime(
    val, raise_on_error: bool = False, tz: tzinfo | str | None = None
) -> datetime | None:
    """Parse a string into a datetime; return None if unparseable (or raise if raise_on_error)."""
    try:
        if val is None or not isinstance(val, str) or val.strip() == "":
            return None
        dt = _dateutil_parser.parse(val)
        return dt if tz is None else to_tz(dt, tz=tz)
    except (ParserError, OverflowError, ValueError, TypeError):
        if raise_on_error:
            raise
    return None


def add_to_datetime(
    dt: datetime | None,
    tz: tzinfo | str | None = None,
    weeks: int = 0,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0,
    milliseconds: int = 0,
    microseconds: int = 0,
) -> datetime | None:
    if dt is None:
        return None
    base = to_tz(dt, tz) if tz is not None else dt
    return base + timedelta(
        weeks=weeks,
        days=days,
        hours=hours,
        minutes=minutes,
        seconds=seconds,
        milliseconds=milliseconds,
        microseconds=microseconds,
    )

def to_iso(
    val: datetime | date | str | None,
    sep: str = " ",
    timespec: str = "seconds",
    default: str | datetime | None = None,
) -> str | None:
    """Return an ISO 8601 string for a datetime/date, pass strings through, and map None to None."""

    def _default() -> str | None:
        return (
            to_iso(default, sep=sep, timespec=timespec)
            if isinstance(default, datetime)
            else default
        )

    if val is None:
        return _default()
    if isinstance(val, str):
        v = val.strip()
        return v if v != "" else _default()
    # datetime is a subclass of date — check datetime first so it gets sep/timespec
    if isinstance(val, datetime):
        return val.isoformat(sep=sep, timespec=timespec)
    return val.isoformat()  # plain date: no sep/timespec


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
