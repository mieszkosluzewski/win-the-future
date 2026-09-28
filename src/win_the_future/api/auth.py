from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from win_the_future.db.dependencies import DbSession
from win_the_future.schemas.auth import TokenRead
from win_the_future.security.tokens import create_access_token
from win_the_future.services import user_service

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

OAuth2Form = Annotated[
    OAuth2PasswordRequestForm,
    Depends(),
]


@router.post(
    "/token",
    response_model=TokenRead,
)
def login(
    form_data: OAuth2Form,
    db: DbSession,
) -> TokenRead:
    user = user_service.authenticate_user(
        db,
        email=form_data.username,
        password=form_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        user_id=user.id,
    )

    return TokenRead(
        access_token=access_token,
        token_type="bearer",
    )
