from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from win_the_future.schemas.user import UserCreate
from win_the_future.services import user_service


def test_login_returns_access_token(
    client: TestClient,
    db_session: Session,
) -> None:
    user_service.create_user(
        db_session,
        UserCreate(
            email="test@example.com",
            password="secret-password",
        ),
    )

    response = client.post(
        "/auth/token",
        data={
            "username": "test@example.com",
            "password": "secret-password",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data["access_token"], str)
    assert data["access_token"]
    assert data["token_type"] == "bearer"


def test_login_with_wrong_password_returns_401(
    client: TestClient,
    db_session: Session,
) -> None:
    user_service.create_user(
        db_session,
        UserCreate(
            email="test@example.com",
            password="secret-password",
        ),
    )

    response = client.post(
        "/auth/token",
        data={
            "username": "test@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401


def test_login_with_nonexistent_user_returns_401(
    client: TestClient,
) -> None:
    response = client.post(
        "/auth/token",
        data={
            "username": "missing@example.com",
            "password": "secret-password",
        },
    )

    assert response.status_code == 401
