from fastapi import APIRouter, HTTPException, status

from win_the_future.db.dependencies import DbSession
from win_the_future.models import User
from win_the_future.schemas.user import UserCreate, UserRead
from win_the_future.services import user_service
from win_the_future.services.exceptions import UserAlreadyExistsError

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user_data: UserCreate,
    db: DbSession,
) -> User:
    try:
        return user_service.create_user(
            db,
            user_data,
        )
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists.",
        ) from None
