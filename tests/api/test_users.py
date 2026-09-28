from fastapi.testclient import TestClient


def test_create_user(
    client: TestClient,
) -> None:
    response = client.post(
        "/users",
        json={
            "email": "test@example.com",
            "password": "secret-password",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] is not None
    assert data["email"] == "test@example.com"
    assert "password" not in data
    assert "hashed_password" not in data


def test_create_user_with_existing_email_returns_409(
    client: TestClient,
) -> None:
    payload = {
        "email": "test@example.com",
        "password": "secret-password",
    }

    first_response = client.post(
        "/users",
        json=payload,
    )
    second_response = client.post(
        "/users",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409

    assert second_response.json()["detail"] == "User already exists."


def test_create_user_with_invalid_email_returns_422(
    client: TestClient,
) -> None:
    response = client.post(
        "/users",
        json={
            "email": "not-an-email",
            "password": "secret-password",
        },
    )

    assert response.status_code == 422
