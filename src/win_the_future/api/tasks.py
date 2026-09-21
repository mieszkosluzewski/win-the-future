from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from win_the_future.db.dependencies import DbSession
from win_the_future.models import Task
from win_the_future.schemas.task import TaskCreate, TaskRead, TaskUpdate
from win_the_future.services import day_service
from win_the_future.services.exceptions import (
    DayAlreadyWonError,
    DayNotCurrentError,
    DayNotReadyError,
    InvalidBonusTaskError,
    TaskNotAssignedToDayError,
    TaskNotFoundError,
)

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)


@router.post("", response_model=TaskRead, status_code=201)
def create_task(
    task_data: TaskCreate,
    db: DbSession,
) -> Task:
    task = Task(**task_data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/backlog", response_model=list[TaskRead])
def get_backlog(
    db: DbSession,
) -> list[Task]:
    statement = select(Task).where(Task.day_id.is_(None)).order_by(Task.id)

    return list(db.scalars(statement).all())


@router.get("/{task_id}", response_model=TaskRead)
def get_task(
    task_id: int,
    db: DbSession,
) -> Task:
    statement = select(Task).where(Task.id == task_id)
    task = db.scalar(statement)
    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    return task


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: DbSession,
) -> Task:
    task = get_task(task_id, db=db)
    updates = task_data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    return task


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_task(
    task_id: int,
    db: DbSession,
) -> Response:
    task = get_task(task_id, db=db)

    db.delete(task)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{task_id}/complete", response_model=TaskRead)
def complete_task(
    task_id: int,
    db: DbSession,
) -> Task:
    try:
        return day_service.complete_task(
            db,
            task_id=task_id,
        )
    except TaskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        ) from None
    except TaskNotAssignedToDayError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task is not assigned to a day.",
        ) from None
    except DayNotCurrentError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only tasks for the current day can be completed.",
        ) from None
    except DayNotReadyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Day is not ready.",
        ) from None
    except DayAlreadyWonError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Core tasks cannot be modified after the day is won.",
        ) from None
    except InvalidBonusTaskError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bonus task is not valid for this day.",
        ) from None


@router.put("/{task_id}/uncomplete", response_model=TaskRead)
def uncomplete_task(
    task_id: int,
    db: DbSession,
) -> Task:
    try:
        return day_service.uncomplete_task(
            db,
            task_id=task_id,
        )
    except TaskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        ) from None
    except TaskNotAssignedToDayError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task is not assigned to a day.",
        ) from None
    except DayNotCurrentError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only tasks for the current day can be modified.",
        ) from None
    except DayAlreadyWonError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Core tasks cannot be modified after the day is won.",
        ) from None
    except InvalidBonusTaskError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bonus task is not valid for this day.",
        ) from None
