from datetime import date

import time_machine
from fastapi.testclient import TestClient

from tests.factories import DayFactory, TaskFactory, UserFactory
from win_the_future.models import TaskCategory, User
from win_the_future.security.tokens import create_access_token


def _auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(user_id=user.id)
    return {"Authorization": f"Bearer {token}"}


def test_get_day_by_date_does_not_return_other_users_day(
    client: TestClient,
    auth_headers: dict[str, str],
    user_factory: UserFactory,
    day_factory: DayFactory,
) -> None:
    other_user = user_factory()
    day = day_factory(
        day_date=date(2026, 9, 12),
        user_id=other_user.id,
    )

    response = client.get(
        f"/days/{day.date.isoformat()}",
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_get_days_returns_only_current_users_days(
    client: TestClient,
    auth_user: User,
    auth_headers: dict[str, str],
    user_factory: UserFactory,
    day_factory: DayFactory,
) -> None:
    own_day = day_factory(
        day_date=date(2026, 9, 12),
        user_id=auth_user.id,
    )

    other_user = user_factory()
    day_factory(
        day_date=date(2026, 9, 11),
        user_id=other_user.id,
    )

    response = client.get(
        "/days",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert [day["id"] for day in response.json()] == [own_day.id]


def test_cannot_create_task_for_other_users_day(
    client: TestClient,
    auth_headers: dict[str, str],
    user_factory: UserFactory,
    day_factory: DayFactory,
) -> None:
    other_user = user_factory()
    day = day_factory(user_id=other_user.id)

    response = client.post(
        f"/days/{day.id}/tasks",
        json={
            "title": "Practice bass",
            "category": "mind",
            "estimated_minutes": 30,
        },
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_cannot_assign_other_users_task_to_own_day(
    client: TestClient,
    auth_user: User,
    auth_headers: dict[str, str],
    user_factory: UserFactory,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(user_id=auth_user.id)

    other_user = user_factory()
    task = task_factory(
        day_id=None,
        user_id=other_user.id,
    )

    response = client.put(
        f"/days/{day.id}/tasks/{task.id}",
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_cannot_assign_own_task_to_other_users_day(
    client: TestClient,
    auth_user: User,
    auth_headers: dict[str, str],
    user_factory: UserFactory,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    other_user = user_factory()
    day = day_factory(user_id=other_user.id)

    task = task_factory(
        day_id=None,
        user_id=auth_user.id,
    )

    response = client.put(
        f"/days/{day.id}/tasks/{task.id}",
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_cannot_unassign_other_users_task(
    client: TestClient,
    auth_user: User,
    auth_headers: dict[str, str],
    user_factory: UserFactory,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(user_id=auth_user.id)

    other_user = user_factory()
    task = task_factory(
        day_id=None,
        user_id=other_user.id,
        category=TaskCategory.MIND,
    )

    response = client.delete(
        f"/days/{day.id}/tasks/{task.id}",
        headers=auth_headers,
    )

    assert response.status_code == 404


@time_machine.travel("2026-09-13")
def test_today_is_scoped_per_user(
    client: TestClient,
    auth_headers: dict[str, str],
    user_factory: UserFactory,
) -> None:
    first_response = client.put(
        "/days/today",
        headers=auth_headers,
    )

    other_user = user_factory()
    second_response = client.put(
        "/days/today",
        headers=_auth_headers(other_user),
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert first_response.json()["id"] != second_response.json()["id"]
    assert first_response.json()["date"] == second_response.json()["date"]
