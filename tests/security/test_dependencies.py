import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from tests.factories import UserFactory
from win_the_future.security.dependencies import get_current_user
from win_the_future.security.tokens import create_access_token


def test_get_current_user(
    db_session: Session,
    user_factory: UserFactory,
) -> None:
    user = user_factory()
    token = create_access_token(user_id=user.id)

    current_user = get_current_user(
        token=token,
        db=db_session,
    )

    assert current_user.id == user.id


def test_get_current_user_with_invalid_token_returns_401(
    db_session: Session,
) -> None:
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            token="invalid-token",
            db=db_session,
        )

    assert exc_info.value.status_code == 401


def test_get_current_user_with_missing_user_returns_401(
    db_session: Session,
) -> None:
    token = create_access_token(user_id=999999)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            token=token,
            db=db_session,
        )

    assert exc_info.value.status_code == 401
