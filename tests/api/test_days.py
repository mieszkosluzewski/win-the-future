from datetime import date, timedelta

import pytest
import time_machine
from fastapi.testclient import TestClient

from tests.factories import DayFactory, TaskFactory
from win_the_future.models import TaskCategory, User


@time_machine.travel("2026-09-13")
def test_get_or_create_today_creates_day(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.put(
        "/days/today",
        headers=auth_headers,
    )
    assert response.status_code == 201

    data = response.json()

    assert data["date"] == date.today().isoformat()
    assert data["is_won"] is False
    assert data["required_core_tasks"] == 5
    assert data["tasks"] == []


@time_machine.travel("2026-09-13")
def test_get_or_create_today_is_idempotent(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    first_response = client.put("/days/today", headers=auth_headers)
    second_response = client.put("/days/today", headers=auth_headers)

    assert first_response.status_code == 201
    assert second_response.status_code == 200

    assert second_response.json()["id"] == first_response.json()["id"]
    assert second_response.json()["date"] == first_response.json()["date"]


@time_machine.travel("2026-09-13")
def test_get_or_create_tomorrow_creates_day(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.put("/days/tomorrow", headers=auth_headers)

    assert response.status_code == 201

    data = response.json()

    assert data["date"] == (date.today() + timedelta(days=1)).isoformat()


@time_machine.travel("2026-09-13")
def test_get_or_create_tomorrow_is_idempotent(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    first_response = client.put("/days/tomorrow", headers=auth_headers)
    second_response = client.put("/days/tomorrow", headers=auth_headers)

    assert first_response.status_code == 201
    assert second_response.status_code == 200

    assert second_response.json()["id"] == first_response.json()["id"]


@time_machine.travel("2026-09-13")
def test_get_days_returns_days_sorted_by_date_desc(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    client.put("/days/today", headers=auth_headers)
    client.put("/days/tomorrow", headers=auth_headers)

    response = client.get("/days", headers=auth_headers)

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["date"] == (date.today() + timedelta(days=1)).isoformat()
    assert data[1]["date"] == date.today().isoformat()


@time_machine.travel("2026-09-13")
def test_get_day_by_date(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    create_response = client.put("/days/today", headers=auth_headers)
    day = create_response.json()

    response = client.get(f"/days/{day['date']}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["id"] == day["id"]
    assert response.json()["date"] == day["date"]


@time_machine.travel("2026-09-13")
def test_get_nonexistent_day_returns_404(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    missing_date = date.today() - timedelta(days=30)

    response = client.get(f"/days/{missing_date.isoformat()}", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Day not found."


@time_machine.travel("2026-09-13")
def test_today_and_tomorrow_are_different_days(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    today_response = client.put("/days/today", headers=auth_headers)
    tomorrow_response = client.put("/days/tomorrow", headers=auth_headers)

    assert today_response.json()["id"] != tomorrow_response.json()["id"]
    assert today_response.json()["date"] != tomorrow_response.json()["date"]


def test_create_task_for_day(
    client: TestClient,
    day_factory: DayFactory,
    auth_user: User,
    auth_headers: dict[str, str],
) -> None:
    day = day_factory(user_id=auth_user.id)

    response = client.post(
        f"/days/{day.id}/tasks",
        json={
            "title": "Practice bass",
            "category": "mind",
            "estimated_minutes": 30,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Practice bass"
    assert data["category"] == "mind"
    assert data["estimated_minutes"] == 30
    assert data["day_id"] == day.id
    assert data["is_completed"] is False
    assert data["is_bonus"] is False


def test_create_task_for_nonexistent_day_returns_404(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.post(
        "/days/999/tasks",
        json={
            "title": "Practice bass",
            "category": "mind",
            "estimated_minutes": 30,
        },
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Day not found."


@pytest.mark.parametrize(
    "payload",
    [
        {
            "title": "",
            "category": "mind",
            "estimated_minutes": 30,
        },
        {
            "title": "Practice bass",
            "category": "invalid",
            "estimated_minutes": 30,
        },
        {
            "title": "Practice bass",
            "category": "mind",
            "estimated_minutes": 0,
        },
        {
            "title": "Practice bass",
            "category": "mind",
            "estimated_minutes": 121,
        },
    ],
)
def test_create_task_for_day_rejects_invalid_task(
    client: TestClient,
    day_factory: DayFactory,
    payload: dict[str, object],
    auth_headers: dict[str, str],
    auth_user: User,
) -> None:
    day = day_factory(user_id=auth_user.id)

    response = client.post(
        f"/days/{day.id}/tasks",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_assign_backlog_task_to_day(
    client: TestClient,
    day_factory: DayFactory,
    task_factory: TaskFactory,
    auth_headers: dict[str, str],
    auth_user: User,
) -> None:
    day = day_factory(user_id=auth_user.id)

    task = task_factory(
        title="Practice bass",
        category=TaskCategory.MIND,
        day_id=None,
        user_id=auth_user.id,
    )

    response = client.put(f"/days/{day.id}/tasks/{task.id}", headers=auth_headers)

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == task.id
    assert data["day_id"] == day.id


def test_assign_task_to_nonexistent_day_returns_404(
    client: TestClient,
    task_factory: TaskFactory,
    auth_headers: dict[str, str],
    auth_user: User,
) -> None:
    task = task_factory(user_id=auth_user.id)

    response = client.put(f"/days/999/tasks/{task.id}", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Day not found."


def test_assign_nonexistent_task_returns_404(
    client: TestClient,
    day_factory: DayFactory,
    auth_user: User,
    auth_headers: dict[str, str],
) -> None:
    day = day_factory(user_id=auth_user.id)

    response = client.put(
        f"/days/{day.id}/tasks/999",
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found."


def test_assign_task_moves_it_from_another_day(
    client: TestClient,
    day_factory: DayFactory,
    task_factory: TaskFactory,
    auth_user: User,
    auth_headers: dict[str, str],
) -> None:
    first_day = day_factory(
        day_date=date(2026, 9, 13),
        user_id=auth_user.id,
    )
    second_day = day_factory(
        day_date=date(2026, 9, 14),
        user_id=auth_user.id,
    )

    task = task_factory(
        day_id=first_day.id,
        user_id=auth_user.id,
    )

    response = client.put(
        f"/days/{second_day.id}/tasks/{task.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["day_id"] == second_day.id


def test_assign_task_to_same_day_is_idempotent(
    client: TestClient,
    day_factory: DayFactory,
    task_factory: TaskFactory,
    auth_user: User,
    auth_headers: dict[str, str],
) -> None:
    day = day_factory(user_id=auth_user.id)

    task = task_factory(
        day_id=day.id,
        user_id=auth_user.id,
    )

    response = client.put(
        f"/days/{day.id}/tasks/{task.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["day_id"] == day.id


def test_unassign_task_from_day(
    client: TestClient,
    day_factory: DayFactory,
    task_factory: TaskFactory,
    auth_user: User,
    auth_headers: dict[str, str],
) -> None:
    day = day_factory(user_id=auth_user.id)

    task = task_factory(
        day_id=day.id,
        user_id=auth_user.id,
    )

    response = client.delete(
        f"/days/{day.id}/tasks/{task.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == task.id
    assert data["day_id"] is None


def test_unassign_task_from_nonexistent_day_returns_404(
    client: TestClient,
    task_factory: TaskFactory,
    auth_user: User,
    auth_headers: dict[str, str],
) -> None:
    task = task_factory(user_id=auth_user.id)

    response = client.delete(
        f"/days/999/tasks/{task.id}",
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Day not found."


def test_unassign_nonexistent_task_returns_404(
    client: TestClient,
    day_factory: DayFactory,
    auth_user: User,
    auth_headers: dict[str, str],
) -> None:
    day = day_factory(user_id=auth_user.id)

    response = client.delete(
        f"/days/{day.id}/tasks/999",
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found."


def test_unassign_task_from_wrong_day_returns_409(
    client: TestClient,
    day_factory: DayFactory,
    task_factory: TaskFactory,
    auth_user: User,
    auth_headers: dict[str, str],
) -> None:
    first_day = day_factory(
        day_date=date(2026, 9, 13),
        user_id=auth_user.id,
    )
    second_day = day_factory(
        day_date=date(2026, 9, 14),
        user_id=auth_user.id,
    )

    task = task_factory(
        day_id=first_day.id,
        user_id=auth_user.id,
    )

    response = client.delete(
        f"/days/{second_day.id}/tasks/{task.id}",
        headers=auth_headers,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Task is not assigned to this day."


def test_unassign_backlog_task_returns_409(
    client: TestClient,
    day_factory: DayFactory,
    task_factory: TaskFactory,
    auth_user: User,
    auth_headers: dict[str, str],
) -> None:
    day = day_factory(user_id=auth_user.id)

    task = task_factory(
        day_id=None,
        user_id=auth_user.id,
    )

    response = client.delete(
        f"/days/{day.id}/tasks/{task.id}",
        headers=auth_headers,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Task is not assigned to this day."
