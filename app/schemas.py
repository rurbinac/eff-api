from pydantic import BaseModel, EmailStr


class SignInRequest(BaseModel):
    userEmail: EmailStr
    userPassword: str


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
