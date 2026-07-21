from app.exceptions import EFFException


class DraftException(EFFException):
    """Base class for draft-related exceptions."""

    pass


class MemberNotAvailableException(DraftException):
    """Exception raised for invalid draft status operations."""

    def __init__(self, key: str):
        message = f"Member {key} is not available to draft."
        super().__init__(message, status_code=422, legacy_code=115)


class NotAvailableMembersException(DraftException):
    """Exception raised for invalid draft status operations."""

    def __init__(self):
        message = "No available member to draft."
        super().__init__(message, status_code=422, legacy_code=115)


class NotAvailableDraftPositionsException(DraftException):
    """Exception raised for invalid draft status operations."""

    def __init__(self):
        message = "No available draft positions."
        super().__init__(message, status_code=422, legacy_code=115)


class DraftStatusException(DraftException):
    """Exception raised for invalid draft status operations."""

    def __init__(self, draftStatus: str):
        message = f"Draft status {draftStatus} is not valid for this operation."
        super().__init__(message, status_code=409, legacy_code=115)


class NotCommisionerException(DraftException):
    """Exception raised when a user is not a commissioner."""

    def __init__(self):
        message = "User is not a commissioner."
        super().__init__(message, status_code=403, legacy_code=104)


class CannotDraftYetException(DraftException):
    """Exception raised when a user cannot draft."""

    def __init__(self):
        message = "Cannot draft with teams still available."
        super().__init__(message, status_code=409, legacy_code=104)


class CannotDraftException(DraftException):
    """Exception raised when a user cannot draft."""

    def __init__(self):
        message = "Cannot draft."
        super().__init__(message, status_code=409, legacy_code=104)


class NotYourTurnException(DraftException):
    """Exception raised when a user tries to draft out of turn."""

    def __init__(self):
        message = "Cannot draft out of turn."
        super().__init__(message, status_code=409, legacy_code=104)
