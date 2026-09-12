from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from win_the_future.db.dependencies import DbSession
from win_the_future.models import Task
from win_the_future.schemas.task import TaskCreate, TaskRead, TaskUpdate

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
