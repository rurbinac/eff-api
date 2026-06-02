from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Date, DateTime, TinyInteger

from app.database import Base


class User(Base):
    __tablename__ = "Users"

    userID: Mapped[int] = mapped_column(Integer, primary_key=True)
    userEmail: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    userPassword: Mapped[str] = mapped_column(String(255), nullable=False)
    userName: Mapped[str] = mapped_column(String(128), nullable=False)
    userLevel: Mapped[int] = mapped_column(TinyInteger, nullable=False)
    firstName: Mapped[str] = mapped_column(String(50), nullable=False)
    lastName: Mapped[str] = mapped_column(String(50), nullable=False)
    birthday: Mapped[datetime] = mapped_column(Date, nullable=False)
    country: Mapped[str | None] = mapped_column(String(50))
    state: Mapped[str | None] = mapped_column(String(50))
    city: Mapped[str | None] = mapped_column(String(50))
    phoneNumber: Mapped[str | None] = mapped_column(String(15))
    timeZone: Mapped[str | None] = mapped_column(String(20))
    userAvatar: Mapped[str | None] = mapped_column(String(128))
    favoriteTeam: Mapped[str | None] = mapped_column(String(50))
    lastSignInDate: Mapped[datetime | None] = mapped_column(DateTime)
    lastSignInIP: Mapped[str | None] = mapped_column(String(15))
    createdIn: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updatedIn: Mapped[datetime | None] = mapped_column(DateTime)
