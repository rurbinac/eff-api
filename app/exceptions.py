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

class NotYourTeamException(EFFException):
    """Exception raised when a user cannot draft."""

    def __init__(self):
        message = "You are not the owner of this team."
        super().__init__(message, status_code=403, legacy_code=104)

class NotAMemberException(EFFException):
    """Exception raised when a user cannot draft."""

    def __init__(self, object_name: str):
        message = f"You are not a member of this {object_name}."
        super().__init__(message, status_code=403, legacy_code=104)

class NotACommissionerException(EFFException):
    """Exception raised when a user cannot draft."""

    def __init__(self, object_name: str = None):
        if object_name is None:
            message = "You are not a commissioner."
        else:
            message = f"You are not a commissioner of this {object_name}."
        super().__init__(message, status_code=403, legacy_code=104)

class NotFoundException(EFFException):
    """Exception raised when a requested resource is not found."""

    def __init__(self, object_name: str | None = None):
        if object_name is None:
            message = "Resource not found."
        else:
            message = f"{object_name} not found."
        super().__init__(message, status_code=404, legacy_code=404)
