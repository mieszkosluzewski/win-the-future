from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from win_the_future.db.base import Base

if TYPE_CHECKING:
    from win_the_future.models import Day, Task


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    hashed_password: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    tasks: Mapped[list[Task]] = relationship(
        back_populates="user",
    )
    days: Mapped[list[Day]] = relationship(
        back_populates="user",
    )
