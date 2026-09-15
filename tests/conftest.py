from collections.abc import Generator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from tests.factories import DayFactory, TaskFactory

# Makes sure all models are registered in Base.metadata.
from win_the_future import models  # noqa: F401
from win_the_future.db.base import Base
from win_the_future.db.dependencies import get_db
from win_the_future.main import app
from win_the_future.models import Day, Task, TaskCategory


@pytest.fixture
def test_engine() -> Generator[Engine, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    yield engine

    Base.metadata.drop_all(engine)
    engine.dispose()



@pytest.fixture
def db_session(test_engine: Engine) -> Generator[Session]:
    session_factory = sessionmaker(
        bind=test_engine,
        autoflush=False,
        expire_on_commit=False,
    )

    with session_factory() as session:
        yield session


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


@pytest.fixture
def day_factory(db_session: Session) -> DayFactory:
    def _make(
        *,
        day_date: date = date(2026, 9, 13),
        required_core_tasks: int = 5,
        is_won: bool = False,
    ) -> Day:
        day = Day(
            date=day_date,
            required_core_tasks=required_core_tasks,
            is_won=is_won,
        )

        db_session.add(day)
        db_session.commit()
        db_session.refresh(day)

        return day

    return _make
