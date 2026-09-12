from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import TaskFactory
from tests.factories import make_task_payload
from win_the_future.models import Day, Task, TaskCategory


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
def test_create_task_invalid_estimated_minutes(client: TestClient, estimated_minutes: int) -> None:
    payload = make_task_payload(estimated_minutes=estimated_minutes)
    response = client.post(
        "/tasks/",
        json=payload,
    )
    assert response.status_code == 422


@pytest.mark.parametrize("title", ["", "    ", None])
def test_create_task_empty_title(client: TestClient, title: str | None) -> None:
    response = client.post("/tasks", json=make_task_payload(title=title))
    assert response.status_code == 422


@pytest.mark.parametrize("estimated_minutes", [1, 120])
def test_create_task_valid_estimated_minutes(client: TestClient, estimated_minutes: int) -> None:
    response = client.post("tasks", json=make_task_payload(estimated_minutes=estimated_minutes))
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
    payload_1 = make_task_payload(title="1")
    payload_2 = make_task_payload(title="2")
    client.post(
        "/tasks",
        json=payload_1,
    )
    client.post(
        "/tasks",
        json=payload_2,
    )
    response = client.get("/tasks/backlog")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 2
    assert {task["title"] for task in data} == {"1", "2"}


def test_get_backlog_returns_only_unassigned_tasks(
    client: TestClient,
    db_session: Session,
) -> None:
    # Unassigned Task
    client.post(
        "/tasks",
        json=make_task_payload(title="Backlog task"),
    )

    # Task Assigned to a Day
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
        json={"is_completed": True},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["is_completed"] is True


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
        json={"is_completed": True},
    )

    data = response.json()

    assert data["title"] == "Original title"
    assert data["category"] == "body"
    assert data["estimated_minutes"] == 45


def test_update_nonexistent_task(
    client: TestClient,
) -> None:
    response = client.patch(
        "/tasks/999999",
        json={"is_completed": True},
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
