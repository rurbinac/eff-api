from contextvars import ContextVar
from datetime import datetime, timezone

from app.utils.dt import utc_now

# Context variable to store the request datetime across the request lifecycle
_request_datetime: ContextVar[datetime | None] = ContextVar('request_datetime', default=None)


class RequestContext:
    """Manages request-scoped data like the current datetime."""

    @classmethod
    def set_datetime(cls, dt: datetime | None = None) -> None:
        """Set the request datetime (should be called once at request start)."""
        if dt is None:
            dt = utc_now()
        _request_datetime.set(dt)

    @classmethod
    def get_datetime(cls) -> datetime:
        """Get the cached request datetime, or create it if not set."""
        dt = _request_datetime.get()
        if dt is None:
            dt = utc_now()
            _request_datetime.set(dt)
        return dt

    @classmethod
    def reset(cls) -> None:
        """Reset the context (useful for testing)."""
        _request_datetime.set(None)

    @staticmethod
    def parse_datetime(dt_str: str) -> datetime:
        """Parse datetime string to a naive UTC datetime.

        Accepts ISO format (with or without timezone) and MySQL
        'YYYY-MM-DD HH:MM:SS' format. Aware datetimes are converted to UTC
        before stripping tzinfo, keeping the naive-UTC convention.
        """
        # Try ISO format first (may include timezone offset)
        try:
            dt = datetime.fromisoformat(dt_str)
            if dt.tzinfo is not None:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt
        except ValueError:
            pass

        # Try MySQL datetime format — always treated as UTC by convention
        try:
            return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise ValueError(f"Invalid datetime format: {dt_str}")


def extract_match_day_status(match_day_data: dict) -> dict:
    """
    Extract and transform MatchDaysStatus data into the response format.

    Extracts matchDayStatus, matchDayStatusStart, matchDayStatusFinish and removes
    the individual start/finish fields. Can be used by any endpoint needing this format.

    Args:
        match_day_data: Dictionary potentially containing MatchDaysStatus fields

    Returns:
        Dictionary with transformed MatchDaysStatus fields
    """
    if not match_day_data:
        return {}

    result = {}

    # Transform scriptStatus to matchDayStatus
    if 'scriptsStatus' in match_day_data:
        result['matchDayStatus'] = match_day_data['scriptsStatus']

    # Transform startMatchDay to matchDayStatusStart
    if match_day_data.get('startMatchDay'):
        result['matchDayStatusStart'] = match_day_data['startMatchDay'].isoformat() \
            if isinstance(match_day_data['startMatchDay'], datetime) \
            else match_day_data['startMatchDay']

    # Transform finishMatchDay to matchDayStatusFinish
    if match_day_data.get('finishMatchDay'):
        result['matchDayStatusFinish'] = match_day_data['finishMatchDay'].isoformat() \
            if isinstance(match_day_data['finishMatchDay'], datetime) \
            else match_day_data['finishMatchDay']

    return result
