from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from win_the_future.models import Task, TaskCategory
from win_the_future.models.day import Day
from win_the_future.schemas.task import TaskCreate
from win_the_future.services.exceptions import (
    DayNotFoundError,
    TaskNotAssignedToDayError,
    TaskNotFoundError, DayNotReadyError, DayAlreadyWonError, InvalidBonusTaskError, CoreTaskLimitReachedError,
)


def _get_core_tasks(day: Day) -> list[Task]:
    return [
        task
        for task in day.tasks
        if not task.is_bonus
    ]


def get_or_create_day(
    db: Session,
    *,
    day_date: date,
) -> tuple[Day, bool]:
    day = db.scalar(select(Day).where(Day.date == day_date))

    if day is not None:
        return day, False

    day = Day(
        date=day_date,
    )

    db.add(day)
    db.commit()
    db.refresh(day)

    return day, True


def get_or_create_today(
    db: Session,
) -> tuple[Day, bool]:
    return get_or_create_day(
        db,
        day_date=date.today(),
    )


def get_or_create_tomorrow(
    db: Session,
) -> tuple[Day, bool]:
    return get_or_create_day(
        db,
        day_date=date.today() + timedelta(days=1),
    )


def get_days(db: Session) -> list[Day]:
    statement = select(Day).order_by(Day.date.desc())
    return list(db.scalars(statement).all())


def get_day_by_date(
    db: Session,
    *,
    day_date: date,
) -> Day | None:
    statement = select(Day).where(Day.date == day_date)
    return db.scalar(statement)


def create_task_for_day(
    db: Session,
    *,
    day_id: int,
    task_data: TaskCreate,
) -> Task:
    day = db.get(Day, day_id)

    if day is None:
        raise DayNotFoundError

    if not day.is_won and len(_get_core_tasks(day)) >= day.required_core_tasks:
        raise CoreTaskLimitReachedError

    task = Task(
        **task_data.model_dump(),
        day_id=day.id,
    )
    if day.is_won:
        task.is_bonus = True

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


def assign_task_to_day(
    db: Session,
    *,
    day_id: int,
    task_id: int,
) -> Task:
    day = db.get(Day, day_id)

    if day is None:
        raise DayNotFoundError

    task = db.get(Task, task_id)

    if task is None:
        raise TaskNotFoundError

    if task in day.tasks:
        return task

    if not task.is_bonus and task.day and task.day.is_won:
        raise DayAlreadyWonError

    task.day_id = day.id

    if day.is_won:
        task.is_bonus = True

    elif len(_get_core_tasks(day)) >= day.required_core_tasks:
        raise CoreTaskLimitReachedError

    else:
        task.is_bonus = False

    db.commit()
    db.refresh(task)

    return task


def unassign_task_from_day(
    db: Session,
    *,
    day_id: int,
    task_id: int,
) -> Task:
    day = db.get(Day, day_id)

    if day is None:
        raise DayNotFoundError

    task = db.get(Task, task_id)

    if task is None:
        raise TaskNotFoundError

    if task.day_id != day.id:
        raise TaskNotAssignedToDayError

    if day.is_won and not task.is_bonus:
        raise DayAlreadyWonError

    task.day_id = None
    task.is_bonus = False

    db.commit()
    db.refresh(task)

    return task


def is_day_ready(
    day: Day,
) -> bool:
    core_tasks = _get_core_tasks(day)

    has_required_task_count = (
        len(core_tasks) == day.required_core_tasks
    )

    categories = {
        task.category
        for task in core_tasks
    }

    has_all_categories = set(TaskCategory) <= categories

    return has_required_task_count and has_all_categories


def _get_task_with_day(
    db: Session,
    *,
    task_id: int,
) -> tuple[Task, Day]:
    task = db.get(Task, task_id)

    if task is None:
        raise TaskNotFoundError

    day = task.day

    if day is None:
        raise TaskNotAssignedToDayError

    return task, day


def _validate_task_modification(
    task: Task,
    day: Day,
) -> None:
    if task.is_bonus and not day.is_won:
            raise InvalidBonusTaskError

    elif day.is_won and not task.is_bonus:
        raise DayAlreadyWonError

def _validate_core_task_completion(
    day: Day,
) -> None:
    if not is_day_ready(day):
        raise DayNotReadyError


def complete_task(
    db: Session,
    *,
    task_id: int,
) -> Task:
    task, day = _get_task_with_day(
        db,
        task_id=task_id,
    )
    if task.is_completed:
        return task

    _validate_task_modification(task, day)

    if not task.is_bonus:
        _validate_core_task_completion(day)

    task.is_completed = True

    if not task.is_bonus and all(
        day_task.is_completed
        for day_task in day.tasks
        if not day_task.is_bonus
    ):
        day.is_won = True

    db.commit()
    db.refresh(task)

    return task


def uncomplete_task(
    db: Session,
    *,
    task_id: int,
) -> Task:
    task, day = _get_task_with_day(
        db,
        task_id=task_id,
    )

    _validate_task_modification(task, day)

    task.is_completed = False

    db.commit()
    db.refresh(task)

    return task