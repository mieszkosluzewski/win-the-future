from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from win_the_future.db.dependencies import DbSession
from win_the_future.models import User
from win_the_future.security.tokens import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token",
)

Token = Annotated[str, Depends(oauth2_scheme)]


def get_current_user(
    token: Token,
    db: DbSession,
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        user_id = decode_access_token(token)
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise credentials_exception from None

    user = db.get(User, user_id)

    if user is None:
        raise credentials_exception

    return user


CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]
