from datetime import date, timedelta

import pytest
import time_machine
from fastapi.testclient import TestClient

from tests.factories import DayFactory, TaskFactory
from win_the_future.models import TaskCategory


@time_machine.travel("2026-09-13")
def test_get_or_create_today_creates_day(
    client: TestClient,
) -> None:
    response = client.put("/days/today")

    assert response.status_code == 201

    data = response.json()

    assert data["date"] == date.today().isoformat()
    assert data["is_won"] is False
    assert data["required_core_tasks"] == 5
    assert data["tasks"] == []


@time_machine.travel("2026-09-13")
def test_get_or_create_today_is_idempotent(
    client: TestClient,
) -> None:
    first_response = client.put("/days/today")
    second_response = client.put("/days/today")

    assert first_response.status_code == 201
    assert second_response.status_code == 200

    assert second_response.json()["id"] == first_response.json()["id"]
    assert second_response.json()["date"] == first_response.json()["date"]


@time_machine.travel("2026-09-13")
def test_get_or_create_tomorrow_creates_day(
    client: TestClient,
) -> None:
    response = client.put("/days/tomorrow")

    assert response.status_code == 201

    data = response.json()

    assert data["date"] == (date.today() + timedelta(days=1)).isoformat()


@time_machine.travel("2026-09-13")
def test_get_or_create_tomorrow_is_idempotent(
    client: TestClient,
) -> None:
    first_response = client.put("/days/tomorrow")
    second_response = client.put("/days/tomorrow")

    assert first_response.status_code == 201
    assert second_response.status_code == 200

    assert second_response.json()["id"] == first_response.json()["id"]


@time_machine.travel("2026-09-13")
def test_get_days_returns_days_sorted_by_date_desc(
    client: TestClient,
) -> None:
    client.put("/days/today")
    client.put("/days/tomorrow")

    response = client.get("/days")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["date"] == (date.today() + timedelta(days=1)).isoformat()
    assert data[1]["date"] == date.today().isoformat()


@time_machine.travel("2026-09-13")
def test_get_day_by_date(
    client: TestClient,
) -> None:
    create_response = client.put("/days/today")
    day = create_response.json()

    response = client.get(f"/days/{day['date']}")

    assert response.status_code == 200
    assert response.json()["id"] == day["id"]
    assert response.json()["date"] == day["date"]


@time_machine.travel("2026-09-13")
def test_get_nonexistent_day_returns_404(
    client: TestClient,
) -> None:
    missing_date = date.today() - timedelta(days=30)

    response = client.get(f"/days/{missing_date.isoformat()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Day not found."


@time_machine.travel("2026-09-13")
def test_today_and_tomorrow_are_different_days(
    client: TestClient,
) -> None:
    today_response = client.put("/days/today")
    tomorrow_response = client.put("/days/tomorrow")

    assert today_response.json()["id"] != tomorrow_response.json()["id"]
    assert today_response.json()["date"] != tomorrow_response.json()["date"]


def test_create_task_for_day(
    client: TestClient,
    day_factory: DayFactory,
) -> None:
    day = day_factory()

    response = client.post(
        f"/days/{day.id}/tasks",
        json={
            "title": "Practice bass",
            "category": "mind",
            "estimated_minutes": 30,
        },
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
) -> None:
    response = client.post(
        "/days/999/tasks",
        json={
            "title": "Practice bass",
            "category": "mind",
            "estimated_minutes": 30,
        },
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
) -> None:
    day = day_factory()

    response = client.post(
        f"/days/{day.id}/tasks",
        json=payload,
    )

    assert response.status_code == 422


def test_assign_backlog_task_to_day(
    client: TestClient,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory()

    task = task_factory(
        title="Practice bass",
        category=TaskCategory.MIND,
        day_id=None,
    )

    response = client.put(f"/days/{day.id}/tasks/{task.id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == task.id
    assert data["day_id"] == day.id


def test_assign_task_to_nonexistent_day_returns_404(
    client: TestClient,
    task_factory: TaskFactory,
) -> None:
    task = task_factory()

    response = client.put(f"/days/999/tasks/{task.id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Day not found."


def test_assign_nonexistent_task_returns_404(
    client: TestClient,
    day_factory: DayFactory,
) -> None:
    day = day_factory()

    response = client.put(f"/days/{day.id}/tasks/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found."


def test_assign_task_moves_it_from_another_day(
    client: TestClient,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    first_day = day_factory(
        day_date=date(2026, 9, 13),
    )
    second_day = day_factory(
        day_date=date(2026, 9, 14),
    )

    task = task_factory(
        day_id=first_day.id,
    )

    response = client.put(f"/days/{second_day.id}/tasks/{task.id}")

    assert response.status_code == 200
    assert response.json()["day_id"] == second_day.id


def test_assign_task_to_same_day_is_idempotent(
    client: TestClient,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory()

    task = task_factory(
        day_id=day.id,
    )

    response = client.put(f"/days/{day.id}/tasks/{task.id}")

    assert response.status_code == 200
    assert response.json()["day_id"] == day.id


def test_unassign_task_from_day(
    client: TestClient,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory()

    task = task_factory(
        day_id=day.id,
    )

    response = client.delete(f"/days/{day.id}/tasks/{task.id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == task.id
    assert data["day_id"] is None


def test_unassign_task_from_nonexistent_day_returns_404(
    client: TestClient,
    task_factory: TaskFactory,
) -> None:
    task = task_factory()

    response = client.delete(f"/days/999/tasks/{task.id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Day not found."


def test_unassign_nonexistent_task_returns_404(
    client: TestClient,
    day_factory: DayFactory,
) -> None:
    day = day_factory()

    response = client.delete(f"/days/{day.id}/tasks/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found."


def test_unassign_task_from_wrong_day_returns_409(
    client: TestClient,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    first_day = day_factory(
        day_date=date(2026, 9, 13),
    )
    second_day = day_factory(
        day_date=date(2026, 9, 14),
    )

    task = task_factory(
        day_id=first_day.id,
    )

    response = client.delete(f"/days/{second_day.id}/tasks/{task.id}")

    assert response.status_code == 409
    assert response.json()["detail"] == ("Task is not assigned to this day.")


def test_unassign_backlog_task_returns_409(
    client: TestClient,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory()

    task = task_factory(
        day_id=None,
    )

    response = client.delete(f"/days/{day.id}/tasks/{task.id}")

    assert response.status_code == 409
    assert response.json()["detail"] == ("Task is not assigned to this day.")
