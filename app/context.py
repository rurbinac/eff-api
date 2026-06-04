from datetime import datetime
from contextvars import ContextVar
from sqlmodel import SQLModel

# Context variable to store the request datetime across the request lifecycle
_request_datetime: ContextVar[datetime | None] = ContextVar('request_datetime', default=None)


class RequestContext:
    """Manages request-scoped data like the current datetime."""

    @classmethod
    def set_datetime(cls, dt: datetime | None = None) -> None:
        """Set the request datetime (should be called once at request start)."""
        if dt is None:
            dt = datetime.utcnow()
        _request_datetime.set(dt)

    @classmethod
    def get_datetime(cls) -> datetime:
        """Get the cached request datetime, or create it if not set."""
        dt = _request_datetime.get()
        if dt is None:
            dt = datetime.utcnow()
            _request_datetime.set(dt)
        return dt

    @classmethod
    def reset(cls) -> None:
        """Reset the context (useful for testing)."""
        _request_datetime.set(None)

    @staticmethod
    def parse_datetime(dt_str: str) -> datetime:
        """Parse datetime string in format 'YYYY-MM-DD HH:MM:SS' or ISO format."""
        # Try ISO format first
        try:
            return datetime.fromisoformat(dt_str)
        except ValueError:
            pass

        # Try MySQL datetime format
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
    if 'startMatchDay' in match_day_data and match_day_data['startMatchDay']:
        result['matchDayStatusStart'] = match_day_data['startMatchDay'].isoformat() \
            if isinstance(match_day_data['startMatchDay'], datetime) \
            else match_day_data['startMatchDay']

    # Transform finishMatchDay to matchDayStatusFinish
    if 'finishMatchDay' in match_day_data and match_day_data['finishMatchDay']:
        result['matchDayStatusFinish'] = match_day_data['finishMatchDay'].isoformat() \
            if isinstance(match_day_data['finishMatchDay'], datetime) \
            else match_day_data['finishMatchDay']

    return result
