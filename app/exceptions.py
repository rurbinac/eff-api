from fastapi import HTTPException, status


class EFFException(HTTPException):
    """Base class for exceptions in the EFF application."""
    def __init__(self, message: str, status_code: int = 400, legacy_code: int | None = None):
        super().__init__(status_code=status_code, detail=message)
        self.message = message
        self.legacy_code = legacy_code

    def legacy_response(self) -> str:
        """Return a legacy response string for backward compatibility."""
        return str(self.legacy_code)

class UnauthorizedException(EFFException):
    """Exception raised for invalid draft status operations."""

    def __init__(self):
        message = "Unauthorized"
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED, legacy_code=115)

class CannotSaveException(EFFException):
    """Exception raised for invalid draft status operations."""

    def __init__(self, object_name: str, reason: str | None = None):
        message = f"Cannot save {object_name}"
        if reason:
            message += f": {reason} "
        super().__init__(message, status_code=status.HTTP_409_CONFLICT, legacy_code=115)

class NotYourTeamException(EFFException):
    """Exception raised when a user cannot draft."""

    def __init__(self):
        message = "You are not the owner of this team."
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN, legacy_code=104)

class NotAMemberException(EFFException):
    """Exception raised when a user cannot draft."""

    def __init__(self, object_name: str):
        message = f"You are not a member of this {object_name}."
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN, legacy_code=104)

class NotACommissionerException(EFFException):
    """Exception raised when a user cannot draft."""

    def __init__(self, object_name: str | None = None, object_id: int | None = None):
        message = "You are not a commissioner"
        if object_name is None:
            message = f"{message}."
        elif object_id is None:
            message = f"{message} of this {object_name}."
        else:
            message = f"{message} of this {object_name} (id={object_id})."
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN, legacy_code=104)


class ForbiddenException(EFFException):
    """Exception raised when a requested resource is not found."""

    def __init__(self, txt: str | None = None):
        if txt is None:
            message = "Not authorised."
        else:
            message = f"Not authorised ({txt})."
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN, legacy_code=104)

class NotFoundException(EFFException):
    """Exception raised when a requested resource is not found."""

    def __init__(self, object_name: str | None = None, object_id: int | None = None):
        if object_name is None:
            message = "Resource not found."
        elif object_id is None:
            message = f"{object_name} not found."
        else:
            message = f"{object_name} (id={object_id}) not found."
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND, legacy_code=404)

class UnknownActionException(EFFException):
    """Exception raised when a requested resource is not found."""

    def __init__(self, action_name: str | None = None, action_type: str | None = None):
        if action_name is None:
            message = "Unknown action."
        elif action_type is None:
            message = f"Unknown action ({action_name})."
        else:
            message = f"Unknown action ({action_name} - type: {action_type})."
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND, legacy_code=404)

class RequiredValueException(EFFException):
    """Exception raised when a requested resource is not found."""

    def __init__(self, value_name: str | None = None, context: str | None = None):
        if value_name is None:
            message = "Missing value action."
        elif context is None:
            message = f"The value {value_name} is required."
        else:
            message = f"The value {value_name} is required for {context}."
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST, legacy_code=400)

