from datetime import date

from fastapi import APIRouter, HTTPException, Response, status

from win_the_future.db.dependencies import DbSession
from win_the_future.models import Task
from win_the_future.models.day import Day
from win_the_future.schemas.day import DayRead
from win_the_future.schemas.task import TaskCreate, TaskRead
from win_the_future.services import day_service
from win_the_future.services.exceptions import (
    DayNotFoundError,
    TaskNotAssignedToDayError,
    TaskNotFoundError,
)

router = APIRouter(
    prefix="/days",
    tags=["days"],
)


@router.put(
    "/today",
    response_model=DayRead,
)
def get_or_create_today(
    response: Response,
    db: DbSession,
) -> Day:
    day, created = day_service.get_or_create_today(db)

    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK

    return day


@router.put(
    "/tomorrow",
    response_model=DayRead,
)
def get_or_create_tomorrow(
    response: Response,
    db: DbSession,
) -> Day:
    day, created = day_service.get_or_create_tomorrow(db)

    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK

    return day


@router.get(
    "",
    response_model=list[DayRead],
)
def get_days(
    db: DbSession,
) -> list[Day]:
    return day_service.get_days(db)


@router.get(
    "/{day_date}",
    response_model=DayRead,
)
def get_day(
    day_date: date,
    db: DbSession,
) -> Day:
    day = day_service.get_day_by_date(
        db,
        day_date=day_date,
    )

    if day is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Day not found.",
        ) from None

    return day


@router.post(
    "/{day_id}/tasks",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
)
def create_task_for_day(
    day_id: int,
    task_data: TaskCreate,
    db: DbSession,
) -> Task:
    try:
        return day_service.create_task_for_day(
            db,
            day_id=day_id,
            task_data=task_data,
        )
    except DayNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Day not found.",
        ) from None


@router.put(
    "/{day_id}/tasks/{task_id}",
    response_model=TaskRead,
)
def assign_task_to_day(
    day_id: int,
    task_id: int,
    db: DbSession,
) -> Task:
    try:
        return day_service.assign_task_to_day(
            db,
            day_id=day_id,
            task_id=task_id,
        )
    except DayNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Day not found.",
        ) from None
    except TaskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        ) from None


@router.delete(
    "/{day_id}/tasks/{task_id}",
    response_model=TaskRead,
)
def unassign_task_from_day(
    day_id: int,
    task_id: int,
    db: DbSession,
) -> Task:
    try:
        return day_service.unassign_task_from_day(
            db,
            day_id=day_id,
            task_id=task_id,
        )
    except DayNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Day not found.",
        ) from None
    except TaskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        ) from None
    except TaskNotAssignedToDayError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task is not assigned to this day.",
        ) from None
