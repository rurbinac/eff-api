from fastapi import HTTPException


class EFFException(HTTPException):
    """Base class for exceptions in the EFF application."""
    def __init__(self, message: str, status_code: int = 400, legacy_code: int | None = None):
        super().__init__(status_code=status_code, detail=message)
        self.message = message
        self.legacy_code = legacy_code

    def legacy_response(self) -> str:
        """Return a legacy response string for backward compatibility."""
        return str(self.legacy_code)


class CannotSaveException(EFFException):
    """Exception raised for invalid draft status operations."""

    def __init__(self, object_name: str, reason: str | None = None):
        message = f"Cannot save {object_name}"
        if reason:
            message += f": {reason} "
        super().__init__(message, status_code=409, legacy_code=115)
