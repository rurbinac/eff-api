from datetime import datetime
from contextvars import ContextVar

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
