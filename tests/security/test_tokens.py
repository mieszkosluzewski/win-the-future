from datetime import timedelta

import jwt
import pytest

from win_the_future.security.tokens import create_access_token, decode_access_token


def test_create_and_decode_access_token() -> None:
    token = create_access_token(user_id=123)

    user_id = decode_access_token(token)

    assert user_id == 123


def test_decode_expired_access_token_raises_error() -> None:
    token = create_access_token(
        user_id=123,
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)
