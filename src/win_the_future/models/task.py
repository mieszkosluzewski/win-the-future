from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Enum, ForeignKey, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from win_the_future.db.base import Base

if TYPE_CHECKING:
    from win_the_future.models.day import Day


class TaskCategory(StrEnum):
    MIND = "mind"
    BODY = "body"
    MONEY = "money"


class Task(Base):
    __tablename__ = "tasks"

    __table_args__ = (
        CheckConstraint(
            "estimated_minutes IS NULL OR (estimated_minutes > 0 AND estimated_minutes <= 120)",
            name="check_task_estimated_minutes",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    day_id: Mapped[int | None] = mapped_column(
        ForeignKey("days.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    title: Mapped[str]

    category: Mapped[TaskCategory] = mapped_column(
        Enum(TaskCategory, name="task_category"),
        nullable=False,
    )

    is_completed: Mapped[bool] = mapped_column(
        default=False,
        server_default=false(),
        nullable=False,
    )

    is_bonus: Mapped[bool] = mapped_column(
        default=False,
        server_default=false(),
        nullable=False,
    )

    estimated_minutes: Mapped[int | None]

    day: Mapped["Day"] = relationship(
        back_populates="tasks",
    )
