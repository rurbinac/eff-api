from pydantic import BaseModel, EmailStr
from datetime import datetime


class SignInRequest(BaseModel):
    userEmail: EmailStr
    userPassword: str


class SignUpRequest(BaseModel):
    userEmail: EmailStr
    userPassword: str
    userName: str = ""
    firstName: str
    lastName: str
    birthday: datetime | None = None
    country: str | None = None
    state: str | None = None
    city: str | None = None
    phoneNumber: str | None = None
    timeZone: str | None = None
    favoriteTeam: str | None = None


class LeaguesBuildRequest(BaseModel):
    leagueName: str
    leaguePassword: str
    leagueType: int
    gameType: int
    scoringSystem: int
    tradeDeadline: datetime
    publishLeague: int
    seasonStatus: int
    teamsPerDivision: str  # CSV format: "8,10,8"


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
