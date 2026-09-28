from fastapi.testclient import TestClient

from win_the_future.models import User


def test_get_current_user(
    client: TestClient,
    auth_user: User,
    auth_headers: dict[str, str],
) -> None:
    response = client.get(
        "/users/me",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": auth_user.id,
        "email": auth_user.email,
    }


def test_get_current_user_without_auth_returns_401(
    client: TestClient,
) -> None:
    response = client.get("/users/me")

    assert response.status_code == 401
