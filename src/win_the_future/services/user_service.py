from sqlalchemy import select
from sqlalchemy.orm import Session

from win_the_future.models.user import User
from win_the_future.schemas.user import UserCreate
from win_the_future.security.passwords import hash_password, verify_password
from win_the_future.services.exceptions import UserAlreadyExistsError


def create_user(
    db: Session,
    user_data: UserCreate,
) -> User:
    existing_user = db.scalar(select(User).where(User.email == user_data.email))

    if existing_user is not None:
        raise UserAlreadyExistsError

    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    user = db.scalar(select(User).where(User.email == email))

    if user is None:
        return None

    if user.hashed_password is None:
        return None

    if not verify_password(
        password,
        user.hashed_password,
    ):
        return None

    return user
