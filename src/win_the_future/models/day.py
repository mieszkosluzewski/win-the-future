from datetime import date as dt_date
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from win_the_future.db.base import Base

if TYPE_CHECKING:
    from win_the_future.models.task import Task
    from win_the_future.models.user import User


class Day(Base):
    __tablename__ = "days"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "date",
            name="uq_days_user_id_date",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    date: Mapped[dt_date] = mapped_column(nullable=False)

    is_won: Mapped[bool] = mapped_column(default=False, server_default=false(), nullable=False)

    tasks: Mapped[list["Task"]] = relationship(back_populates="day")

    required_core_tasks: Mapped[int] = mapped_column(
        default=5,
        server_default="5",
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            name="fk_days_user_id_users",
        ),
        index=True,
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="days",
    )
