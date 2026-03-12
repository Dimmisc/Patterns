import datetime
from typing import List, Dict
from sqlalchemy import ForeignKey, DateTime, Date, Boolean, Integer, JSON, String
from sqlalchemy import Enum as SEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from enums import UserRole


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(), nullable=False)
    surname: Mapped[str] = mapped_column(String(), nullable=False)
    patronymic: Mapped[str | None] = mapped_column(String())
    email: Mapped[str] = mapped_column(String(), nullable=False)
    password: Mapped[str] = mapped_column(String(), nullable=False)
    registered_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.now, nullable=False)
    role: Mapped[UserRole] = mapped_column(SEnum(UserRole), default=UserRole.USER, nullable=False)
    banned: Mapped[bool] = mapped_column(Boolean(), default=False, nullable=False)
    balance: Mapped[int] = mapped_column(Integer(), default=0)


class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    jti: Mapped[str] = mapped_column(String(), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


# from enum import Enum
# class Some(str, Enum):
#     pass

# class Predmet(Base):
#     __tablename__ = "predmets"
#     id: Mapped[int] = mapped_column(primary_key=True)

#     date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
#     enum: Mapped[Some] = mapped_column(SEnum(Some))
#     stris: Mapped[str] = mapped_column(String())
#     ints: Mapped[List[int]] = mapped_column(List[int])
#     requests: Mapped[List[Dict[str, List[str]]]] = mapped_column(JSON)

#     room_id: Mapped[int] = mapped_column(ForeignKey("room.id"))
#     prisnakas: Mapped[List["Prisnak"]] = relationship(back_populates="predmets")