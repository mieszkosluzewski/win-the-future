from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from tests.factories import TaskFactory

# Makes sure all models are registered in Base.metadata.
from win_the_future import models  # noqa: F401
from win_the_future.db.base import Base
from win_the_future.db.dependencies import get_db
from win_the_future.main import app
from win_the_future.models import Task, TaskCategory


@pytest.fixture
def db_session() -> Generator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    with session_factory() as session:
        yield session

    Base.metadata.drop_all(engine)


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient]:
    def override_get_db() -> Generator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def task_factory(
    db_session: Session,
) -> TaskFactory:
    def _make(
        *,
        title: str = "Test task",
        category: TaskCategory = TaskCategory.MIND,
        estimated_minutes: int | None = 30,
        is_completed: bool = False,
        is_bonus: bool = False,
        day_id: int | None = None,
    ) -> Task:
        task = Task(
            title=title,
            category=category,
            estimated_minutes=estimated_minutes,
            is_completed=is_completed,
            is_bonus=is_bonus,
            day_id=day_id,
        )

        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        return task

    return _make
