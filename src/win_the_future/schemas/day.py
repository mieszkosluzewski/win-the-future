from datetime import date

from pydantic import BaseModel, ConfigDict

from win_the_future.schemas.task import TaskRead


class DayCreate(BaseModel):
    date: date
    required_core_tasks: int = 5


class DayRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: date
    is_won: bool
    required_core_tasks: int
    tasks: list[TaskRead]
