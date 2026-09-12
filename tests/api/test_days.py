from datetime import date, timedelta

import time_machine
from fastapi.testclient import TestClient


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
