import pytest
from sqlalchemy.orm import Session

from win_the_future.models.user import User
from win_the_future.schemas.user import UserCreate
from win_the_future.security.passwords import verify_password
from win_the_future.services import user_service
from win_the_future.services.exceptions import UserAlreadyExistsError


def test_create_user(
    db_session: Session,
) -> None:
    user = user_service.create_user(
        db_session,
        UserCreate(
            email="test@example.com",
            password="secret-password",
        ),
    )

    assert user.id is not None
    assert user.email == "test@example.com"

    persisted_user = db_session.get(User, user.id)

    assert persisted_user is not None
    assert persisted_user.email == "test@example.com"


def test_create_user_hashes_password(
    db_session: Session,
) -> None:
    password = "secret-password"

    user = user_service.create_user(
        db_session,
        UserCreate(
            email="test@example.com",
            password=password,
        ),
    )

    assert user.hashed_password is not None
    assert user.hashed_password != password
    assert verify_password(password, user.hashed_password) is True


def test_create_user_with_existing_email_raises_error(
    db_session: Session,
) -> None:
    user_data = UserCreate(
        email="test@example.com",
        password="secret-password",
    )

    user_service.create_user(
        db_session,
        user_data,
    )

    with pytest.raises(UserAlreadyExistsError):
        user_service.create_user(
            db_session,
            user_data,
        )


def test_authenticate_user(
    db_session: Session,
) -> None:
    user = user_service.create_user(
        db_session,
        UserCreate(
            email="test@example.com",
            password="secret-password",
        ),
    )

    authenticated_user = user_service.authenticate_user(
        db_session,
        email="test@example.com",
        password="secret-password",
    )

    assert authenticated_user is not None
    assert authenticated_user.id == user.id


def test_authenticate_user_with_wrong_password_returns_none(
    db_session: Session,
) -> None:
    user_service.create_user(
        db_session,
        UserCreate(
            email="test@example.com",
            password="secret-password",
        ),
    )

    authenticated_user = user_service.authenticate_user(
        db_session,
        email="test@example.com",
        password="wrong-password",
    )

    assert authenticated_user is None


def test_authenticate_nonexistent_user_returns_none(
    db_session: Session,
) -> None:
    authenticated_user = user_service.authenticate_user(
        db_session,
        email="missing@example.com",
        password="secret-password",
    )

    assert authenticated_user is None
