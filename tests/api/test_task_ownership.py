from datetime import date

import time_machine
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import DayFactory, TaskFactory, UserFactory
from win_the_future.models import User
from win_the_future.security.tokens import create_access_token


def _auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(user_id=user.id)
    return {"Authorization": f"Bearer {token}"}


def test_get_other_users_task_returns_404(
    client: TestClient,
    auth_headers: dict[str, str],
    user_factory: UserFactory,
    task_factory: TaskFactory,
) -> None:
    other_user = user_factory()
    task = task_factory(user_id=other_user.id)

    response = client.get(
        f"/tasks/{task.id}",
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_update_other_users_task_returns_404(
    client: TestClient,
    auth_headers: dict[str, str],
    user_factory: UserFactory,
    task_factory: TaskFactory,
) -> None:
    other_user = user_factory()
    task = task_factory(user_id=other_user.id)

    response = client.patch(
        f"/tasks/{task.id}",
        json={"title": "Changed title"},
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_delete_other_users_task_returns_404(
    client: TestClient,
    auth_headers: dict[str, str],
    user_factory: UserFactory,
    task_factory: TaskFactory,
) -> None:
    other_user = user_factory()
    task = task_factory(user_id=other_user.id)

    response = client.delete(
        f"/tasks/{task.id}",
        headers=auth_headers,
    )

    assert response.status_code == 404


@time_machine.travel("2026-09-13")
def test_complete_other_users_task_returns_404(
    client: TestClient,
    auth_headers: dict[str, str],
    user_factory: UserFactory,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    other_user = user_factory()
    day = day_factory(
        day_date=date(2026, 9, 13),
        user_id=other_user.id,
    )
    task = task_factory(
        day_id=day.id,
        user_id=other_user.id,
    )

    response = client.put(
        f"/tasks/{task.id}/complete",
        headers=auth_headers,
    )

    assert response.status_code == 404


@time_machine.travel("2026-09-13")
def test_uncomplete_other_users_task_returns_404(
    client: TestClient,
    auth_headers: dict[str, str],
    user_factory: UserFactory,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    other_user = user_factory()
    day = day_factory(
        day_date=date(2026, 9, 13),
        user_id=other_user.id,
    )
    task = task_factory(
        day_id=day.id,
        user_id=other_user.id,
        is_completed=True,
    )

    response = client.put(
        f"/tasks/{task.id}/uncomplete",
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_backlog_returns_only_current_users_tasks(
    client: TestClient,
    auth_user: User,
    auth_headers: dict[str, str],
    user_factory: UserFactory,
    task_factory: TaskFactory,
) -> None:
    own_task = task_factory(
        title="My backlog task",
        day_id=None,
        user_id=auth_user.id,
    )

    other_user = user_factory()
    task_factory(
        title="Other user's backlog task",
        day_id=None,
        user_id=other_user.id,
    )

    response = client.get(
        "/tasks/backlog",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert [task["id"] for task in response.json()] == [own_task.id]


def test_new_task_belongs_to_current_user(
    client: TestClient,
    auth_user: User,
    auth_headers: dict[str, str],
    db_session: Session,
) -> None:
    response = client.post(
        "/tasks",
        json={
            "title": "My task",
            "category": "mind",
            "estimated_minutes": 30,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201

    from win_the_future.models import Task

    task = db_session.get(Task, response.json()["id"])

    assert task is not None
    assert task.user_id == auth_user.id
