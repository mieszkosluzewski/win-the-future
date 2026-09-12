from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from win_the_future.models.day import Day


def get_or_create_day(
    db: Session,
    *,
    day_date: date,
) -> tuple[Day, bool]:
    day = db.scalar(select(Day).where(Day.date == day_date))

    if day is not None:
        return day, False

    day = Day(
        date=day_date,
    )

    db.add(day)
    db.commit()
    db.refresh(day)

    return day, True


def get_or_create_today(
    db: Session,
) -> tuple[Day, bool]:
    return get_or_create_day(
        db,
        day_date=date.today(),
    )


def get_or_create_tomorrow(
    db: Session,
) -> tuple[Day, bool]:
    return get_or_create_day(
        db,
        day_date=date.today() + timedelta(days=1),
    )


def get_days(db: Session) -> list[Day]:
    statement = select(Day).order_by(Day.date.desc())
    return list(db.scalars(statement).all())


def get_day_by_date(
    db: Session,
    *,
    day_date: date,
) -> Day | None:
    statement = select(Day).where(Day.date == day_date)
    return db.scalar(statement)
