from datetime import date as dt_date
from typing import TYPE_CHECKING

from sqlalchemy import false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from win_the_future.db.base import Base

if TYPE_CHECKING:
    from win_the_future.models.task import Task


class Day(Base):
    __tablename__ = "days"

    id: Mapped[int] = mapped_column(primary_key=True)

    date: Mapped[dt_date] = mapped_column(nullable=False, unique=True)

    is_won: Mapped[bool] = mapped_column(default=False, server_default=false(), nullable=False)

    tasks: Mapped[list["Task"]] = relationship(back_populates="day")
