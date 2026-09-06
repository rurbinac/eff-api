from app.exceptions import EFFException


class ServiceException(EFFException):
    """Base class for draft-related exceptions."""


class FeedParsingException(ServiceException):
    """Exception raised for invalid draft status operations."""

    def __init__(self, feed: str, msg: str | None = None):
        message = f"There is an error parsing the {feed} feed"
        message += f": {msg}" if msg else "."
        super().__init__(message, status_code=422, legacy_code=115)
