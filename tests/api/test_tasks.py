from datetime import date

import pytest
import time_machine
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import DayFactory, TaskFactory, make_task_payload
from win_the_future.models import Day, Task, TaskCategory


def _create_ready_day(
    day_factory: DayFactory,
    task_factory: TaskFactory,
    *,
    day_date: date = date(2026, 9, 13),
) -> tuple[Day, list[Task]]:
    day = day_factory(
        day_date=day_date,
        required_core_tasks=5,
    )
    tasks = [
        task_factory(day_id=day.id, category=TaskCategory.MIND),
        task_factory(day_id=day.id, category=TaskCategory.BODY),
        task_factory(day_id=day.id, category=TaskCategory.MONEY),
        task_factory(day_id=day.id, category=TaskCategory.MIND),
        task_factory(day_id=day.id, category=TaskCategory.MONEY),
    ]
    return day, tasks


def test_create_task(client: TestClient) -> None:
    payload = make_task_payload()
    response = client.post(
        "/tasks",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] is not None
    assert data["title"] == payload["title"]
    assert data["category"] == payload["category"]
    assert data["estimated_minutes"] == payload["estimated_minutes"]
    assert data["day_id"] is None
    assert data["is_completed"] is False
    assert data["is_bonus"] is False


@pytest.mark.parametrize("estimated_minutes", [0, 121, -5])
def test_create_task_invalid_estimated_minutes(
    client: TestClient,
    estimated_minutes: int,
) -> None:
    payload = make_task_payload(estimated_minutes=estimated_minutes)
    response = client.post(
        "/tasks/",
        json=payload,
    )

    assert response.status_code == 422


@pytest.mark.parametrize("title", ["", "    ", None])
def test_create_task_empty_title(
    client: TestClient,
    title: str | None,
) -> None:
    response = client.post(
        "/tasks",
        json=make_task_payload(title=title),
    )

    assert response.status_code == 422


@pytest.mark.parametrize("estimated_minutes", [1, 120])
def test_create_task_valid_estimated_minutes(
    client: TestClient,
    estimated_minutes: int,
) -> None:
    response = client.post(
        "/tasks",
        json=make_task_payload(estimated_minutes=estimated_minutes),
    )

    assert response.status_code == 201


def test_update_task_rejects_null_title(
    client: TestClient,
) -> None:
    create_response = client.post(
        "/tasks",
        json=make_task_payload(),
    )
    task_id = create_response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        json={"title": None},
    )

    assert response.status_code == 422


def test_get_backlog(client: TestClient) -> None:
    client.post(
        "/tasks",
        json=make_task_payload(title="1"),
    )
    client.post(
        "/tasks",
        json=make_task_payload(title="2"),
    )

    response = client.get("/tasks/backlog")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert {task["title"] for task in data} == {"1", "2"}


def test_get_backlog_returns_only_unassigned_tasks(
    client: TestClient,
    db_session: Session,
) -> None:
    client.post(
        "/tasks",
        json=make_task_payload(title="Backlog task"),
    )

    day = Day(date=date(2026, 9, 12))
    assigned_task = Task(
        title="Assigned task",
        category=TaskCategory.MONEY,
        estimated_minutes=30,
        day=day,
    )

    db_session.add_all([day, assigned_task])
    db_session.commit()

    response = client.get("/tasks/backlog")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["title"] == "Backlog task"
    assert data[0]["day_id"] is None


def test_get_task(
    client: TestClient,
    task_factory: TaskFactory,
) -> None:
    task = task_factory()

    response = client.get(f"/tasks/{task.id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == task.id
    assert data["title"] == task.title


def test_get_nonexistent_task(
    client: TestClient,
) -> None:
    response = client.get("/tasks/999999")

    assert response.status_code == 404


def test_update_task_changes_requested_field(
    client: TestClient,
    task_factory: TaskFactory,
) -> None:
    task = task_factory(
        title="Original title",
        estimated_minutes=45,
    )

    response = client.patch(
        f"/tasks/{task.id}",
        json={"title": "Updated title"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Updated title"


def test_update_task_preserves_unspecified_fields(
    client: TestClient,
    task_factory: TaskFactory,
) -> None:
    task = task_factory(
        title="Original title",
        category=TaskCategory.BODY,
        estimated_minutes=45,
    )

    response = client.patch(
        f"/tasks/{task.id}",
        json={"title": "Updated title"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["category"] == "body"
    assert data["estimated_minutes"] == 45
    assert data["is_completed"] is False


def test_update_task_rejects_is_completed(
    client: TestClient,
    task_factory: TaskFactory,
) -> None:
    task = task_factory(is_completed=False)

    response = client.patch(
        f"/tasks/{task.id}",
        json={"is_completed": True},
    )

    assert response.status_code == 422


def test_update_nonexistent_task(
    client: TestClient,
) -> None:
    response = client.patch(
        "/tasks/999999",
        json={"title": "Updated title"},
    )

    assert response.status_code == 404


def test_delete_task(
    client: TestClient,
    task_factory: TaskFactory,
) -> None:
    task = task_factory()

    response = client.delete(f"/tasks/{task.id}")

    assert response.status_code == 204

    get_response = client.get(f"/tasks/{task.id}")

    assert get_response.status_code == 404


def test_delete_nonexistent_task(
    client: TestClient,
) -> None:
    response = client.delete("/tasks/999999")

    assert response.status_code == 404


@time_machine.travel("2026-09-13")
def test_complete_task(
    client: TestClient,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    _, tasks = _create_ready_day(day_factory, task_factory)
    task = tasks[0]

    response = client.put(f"/tasks/{task.id}/complete")

    assert response.status_code == 200
    assert response.json()["is_completed"] is True


@time_machine.travel("2026-09-13")
def test_completing_last_core_task_wins_day(
    client: TestClient,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day, tasks = _create_ready_day(day_factory, task_factory)

    for task in tasks[:-1]:
        task.is_completed = True

    response = client.put(f"/tasks/{tasks[-1].id}/complete")

    assert response.status_code == 200

    day_response = client.get(f"/days/{day.date.isoformat()}")

    assert day_response.status_code == 200
    assert day_response.json()["is_won"] is True


@time_machine.travel("2026-09-13")
def test_complete_nonexistent_task_returns_404(
    client: TestClient,
) -> None:
    response = client.put("/tasks/999999/complete")

    assert response.status_code == 404


@time_machine.travel("2026-09-13")
def test_complete_backlog_task_returns_409(
    client: TestClient,
    task_factory: TaskFactory,
) -> None:
    task = task_factory(day_id=None)

    response = client.put(f"/tasks/{task.id}/complete")

    assert response.status_code == 409


@time_machine.travel("2026-09-13")
def test_complete_task_when_day_is_not_ready_returns_409(
    client: TestClient,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(day_date=date(2026, 9, 13))
    task = task_factory(
        day_id=day.id,
        category=TaskCategory.MIND,
    )

    response = client.put(f"/tasks/{task.id}/complete")

    assert response.status_code == 409


@time_machine.travel("2026-09-13")
def test_complete_core_task_after_day_is_won_returns_409(
    client: TestClient,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(
        day_date=date(2026, 9, 13),
        is_won=True,
    )
    task = task_factory(
        day_id=day.id,
        is_bonus=False,
        is_completed=False,
    )

    response = client.put(f"/tasks/{task.id}/complete")

    assert response.status_code == 409


@time_machine.travel("2026-09-13")
def test_complete_bonus_task_after_day_is_won(
    client: TestClient,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(
        day_date=date(2026, 9, 13),
        is_won=True,
    )
    task = task_factory(
        day_id=day.id,
        is_bonus=True,
        is_completed=False,
    )

    response = client.put(f"/tasks/{task.id}/complete")

    assert response.status_code == 200
    assert response.json()["is_completed"] is True


@time_machine.travel("2026-09-13")
def test_complete_task_for_past_day_returns_409(
    client: TestClient,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day, tasks = _create_ready_day(
        day_factory,
        task_factory,
        day_date=date(2026, 9, 12),
    )

    response = client.put(f"/tasks/{tasks[0].id}/complete")

    assert response.status_code == 409


@time_machine.travel("2026-09-13")
def test_complete_task_for_future_day_returns_409(
    client: TestClient,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day, tasks = _create_ready_day(
        day_factory,
        task_factory,
        day_date=date(2026, 9, 14),
    )

    response = client.put(f"/tasks/{tasks[0].id}/complete")

    assert response.status_code == 409


@time_machine.travel("2026-09-13")
def test_complete_task_is_idempotent(
    client: TestClient,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    _, tasks = _create_ready_day(day_factory, task_factory)
    task = tasks[0]

    first_response = client.put(f"/tasks/{task.id}/complete")
    second_response = client.put(f"/tasks/{task.id}/complete")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json()["is_completed"] is True


@time_machine.travel("2026-09-13")
def test_uncomplete_task(
    client: TestClient,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(day_date=date(2026, 9, 13))
    task = task_factory(
        day_id=day.id,
        is_completed=True,
    )

    response = client.put(f"/tasks/{task.id}/uncomplete")

    assert response.status_code == 200
    assert response.json()["is_completed"] is False


@time_machine.travel("2026-09-13")
def test_uncomplete_nonexistent_task_returns_404(
    client: TestClient,
) -> None:
    response = client.put("/tasks/999999/uncomplete")

    assert response.status_code == 404


@time_machine.travel("2026-09-13")
def test_uncomplete_backlog_task_returns_409(
    client: TestClient,
    task_factory: TaskFactory,
) -> None:
    task = task_factory(
        day_id=None,
        is_completed=True,
    )

    response = client.put(f"/tasks/{task.id}/uncomplete")

    assert response.status_code == 409


@time_machine.travel("2026-09-13")
def test_uncomplete_core_task_after_day_is_won_returns_409(
    client: TestClient,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(
        day_date=date(2026, 9, 13),
        is_won=True,
    )
    task = task_factory(
        day_id=day.id,
        is_bonus=False,
        is_completed=True,
    )

    response = client.put(f"/tasks/{task.id}/uncomplete")

    assert response.status_code == 409


@time_machine.travel("2026-09-13")
def test_uncomplete_bonus_task_after_day_is_won(
    client: TestClient,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(
        day_date=date(2026, 9, 13),
        is_won=True,
    )
    task = task_factory(
        day_id=day.id,
        is_bonus=True,
        is_completed=True,
    )

    response = client.put(f"/tasks/{task.id}/uncomplete")

    assert response.status_code == 200
    assert response.json()["is_completed"] is False


@time_machine.travel("2026-09-13")
def test_uncomplete_task_for_past_day_returns_409(
    client: TestClient,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(day_date=date(2026, 9, 12))
    task = task_factory(
        day_id=day.id,
        is_completed=True,
    )

    response = client.put(f"/tasks/{task.id}/uncomplete")

    assert response.status_code == 409


@time_machine.travel("2026-09-13")
def test_uncomplete_task_for_future_day_returns_409(
    client: TestClient,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(day_date=date(2026, 9, 14))
    task = task_factory(
        day_id=day.id,
        is_completed=True,
    )

    response = client.put(f"/tasks/{task.id}/uncomplete")

    assert response.status_code == 409


@time_machine.travel("2026-09-13")
def test_uncomplete_task_is_idempotent(
    client: TestClient,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(day_date=date(2026, 9, 13))
    task = task_factory(
        day_id=day.id,
        is_completed=False,
    )

    first_response = client.put(f"/tasks/{task.id}/uncomplete")
    second_response = client.put(f"/tasks/{task.id}/uncomplete")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json()["is_completed"] is False
