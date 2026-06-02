from datetime import datetime
from pydantic import BaseModel, EmailStr


class SignInRequest(BaseModel):
    userEmail: EmailStr
    userPassword: str


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    userID: int
    userEmail: str
    userName: str
    userLevel: int
    firstName: str
    lastName: str
    birthday: datetime
    country: str | None = None
    state: str | None = None
    city: str | None = None
    phoneNumber: str | None = None
    timeZone: str | None = None
    userAvatar: str | None = None
    favoriteTeam: str | None = None
    lastSignInDate: datetime | None = None
    lastSignInIP: str | None = None
    createdIn: datetime
    updatedIn: datetime | None = None


class SignInResponse(BaseModel):
    userID: int
    userEmail: str
    userName: str
    firstName: str
    lastName: str
    token: str
    feedsMode: int = 0


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
