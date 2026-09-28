from collections.abc import Generator
from datetime import date
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from tests.factories import DayFactory, TaskFactory, UserFactory

# Makes sure all models are registered in Base.metadata.
from win_the_future import models  # noqa: F401
from win_the_future.db.base import Base
from win_the_future.db.dependencies import get_db
from win_the_future.main import app
from win_the_future.models import Day, Task, TaskCategory, User
from win_the_future.security.tokens import create_access_token


@pytest.fixture
def test_engine() -> Generator[Engine]:
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
def db_session(
    test_engine: Engine,
) -> Generator[Session]:
    session_factory = sessionmaker(
        bind=test_engine,
        autoflush=False,
        expire_on_commit=False,
    )

    with session_factory() as session:
        yield session


@pytest.fixture
def client(
    db_session: Session,
) -> Generator[TestClient]:
    def override_get_db() -> Generator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def user_factory(
    db_session: Session,
) -> UserFactory:
    def _make(
        *,
        email: str | None = None,
        hashed_password: str | None = None,
    ) -> User:
        user = User(
            email=email or f"user-{uuid4()}@example.com",
            hashed_password=hashed_password,
        )

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        return user

    return _make


@pytest.fixture
def day_factory(
    db_session: Session,
    user_factory: UserFactory,
) -> DayFactory:
    def _make(
        *,
        day_date: date = date(2026, 9, 13),
        required_core_tasks: int = 5,
        is_won: bool = False,
        user_id: int | None = None,
    ) -> Day:
        if user_id is None:
            user_id = user_factory().id

        day = Day(
            date=day_date,
            required_core_tasks=required_core_tasks,
            is_won=is_won,
            user_id=user_id,
        )

        db_session.add(day)
        db_session.commit()
        db_session.refresh(day)

        return day

    return _make


@pytest.fixture
def task_factory(
    db_session: Session,
    user_factory: UserFactory,
) -> TaskFactory:
    def _make(
        *,
        title: str = "Test task",
        category: TaskCategory = TaskCategory.MIND,
        estimated_minutes: int | None = 30,
        is_completed: bool = False,
        is_bonus: bool = False,
        day_id: int | None = None,
        user_id: int | None = None,
    ) -> Task:
        if user_id is None:
            if day_id is not None:
                day = db_session.get(Day, day_id)

                if day is None:
                    raise ValueError(f"Day {day_id} does not exist")

                user_id = day.user_id
            else:
                user_id = user_factory().id

        task = Task(
            title=title,
            category=category,
            estimated_minutes=estimated_minutes,
            is_completed=is_completed,
            is_bonus=is_bonus,
            day_id=day_id,
            user_id=user_id,
        )

        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        return task

    return _make


@pytest.fixture
def auth_user(
    user_factory: UserFactory,
) -> User:
    return user_factory()


@pytest.fixture
def auth_headers(
    auth_user: User,
) -> dict[str, str]:
    token = create_access_token(
        user_id=auth_user.id,
    )

    return {
        "Authorization": f"Bearer {token}",
    }
