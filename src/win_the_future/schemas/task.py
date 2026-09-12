from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from win_the_future.models.task import TaskCategory

TaskTitle = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=255,
    ),
]


class TaskCreate(BaseModel):
    title: TaskTitle = Field(min_length=1, max_length=255)
    category: TaskCategory
    estimated_minutes: int | None = Field(
        default=None,
        ge=1,
        le=120,
    )


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    day_id: int | None
    title: TaskTitle
    category: TaskCategory
    is_completed: bool
    is_bonus: bool
    estimated_minutes: int | None


class TaskUpdate(BaseModel):
    title: TaskTitle | None = Field(default=None, min_length=1, max_length=255)
    category: TaskCategory | None = None
    estimated_minutes: int | None = Field(default=None, ge=1, le=120)
    is_completed: bool | None = None

    # noinspection PyNestedDecorators
    @field_validator("title", mode="before")
    @classmethod
    def title_cannot_be_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("title cannot be null")

        return value
