from datetime import date

from fastapi import APIRouter, HTTPException, Response, status

from win_the_future.db.dependencies import DbSession
from win_the_future.models.day import Day
from win_the_future.schemas.day import DayRead
from win_the_future.services import day_service

router = APIRouter(
    prefix="/days",
    tags=["days"],
)


@router.put(
    "/today",
    response_model=DayRead,
)
def get_or_create_today(
    response: Response,
    db: DbSession,
) -> Day:
    day, created = day_service.get_or_create_today(db)

    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK

    return day


@router.put(
    "/tomorrow",
    response_model=DayRead,
)
def get_or_create_tomorrow(
    response: Response,
    db: DbSession,
) -> Day:
    day, created = day_service.get_or_create_tomorrow(db)

    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK

    return day


@router.get(
    "",
    response_model=list[DayRead],
)
def get_days(
    db: DbSession,
) -> list[Day]:
    return day_service.get_days(db)


@router.get(
    "/{day_date}",
    response_model=DayRead,
)
def get_day(
    day_date: date,
    db: DbSession,
) -> Day:
    day = day_service.get_day_by_date(
        db,
        day_date=day_date,
    )

    if day is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Day not found.",
        )

    return day
