from datetime import date

import pytest
from sqlalchemy.orm import Session

from tests.factories import DayFactory, TaskFactory
from win_the_future.models import TaskCategory
from win_the_future.schemas.task import TaskCreate
from win_the_future.services import day_service
from win_the_future.services.exceptions import DayNotReadyError, DayAlreadyWonError, TaskNotAssignedToDayError, \
    TaskNotFoundError, CoreTaskLimitReachedError


def test_day_is_not_ready_with_no_tasks(
    day_factory: DayFactory,
) -> None:
    day = day_factory()

    assert day_service.is_day_ready(day) is False


def test_day_is_not_ready_with_too_few_tasks(
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(required_core_tasks=5)

    task_factory(day_id=day.id, category=TaskCategory.MIND)
    task_factory(day_id=day.id, category=TaskCategory.BODY)
    task_factory(day_id=day.id, category=TaskCategory.MONEY)
    task_factory(day_id=day.id, category=TaskCategory.MIND)

    assert day_service.is_day_ready(day) is False


def test_day_is_not_ready_when_required_category_is_missing(
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(required_core_tasks=5)

    task_factory(day_id=day.id, category=TaskCategory.MIND)
    task_factory(day_id=day.id, category=TaskCategory.MIND)
    task_factory(day_id=day.id, category=TaskCategory.MONEY)
    task_factory(day_id=day.id, category=TaskCategory.MONEY)
    task_factory(day_id=day.id, category=TaskCategory.MONEY)

    assert day_service.is_day_ready(day) is False


def test_day_is_ready_with_required_number_of_tasks_and_all_categories(
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(required_core_tasks=5)

    task_factory(day_id=day.id, category=TaskCategory.MIND)
    task_factory(day_id=day.id, category=TaskCategory.BODY)
    task_factory(day_id=day.id, category=TaskCategory.MONEY)
    task_factory(day_id=day.id, category=TaskCategory.MIND)
    task_factory(day_id=day.id, category=TaskCategory.MONEY)

    assert day_service.is_day_ready(day) is True


def test_bonus_tasks_do_not_count_towards_day_readiness(
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(required_core_tasks=5)

    task_factory(day_id=day.id, category=TaskCategory.MIND)
    task_factory(day_id=day.id, category=TaskCategory.BODY)
    task_factory(day_id=day.id, category=TaskCategory.MONEY)
    task_factory(day_id=day.id, category=TaskCategory.MIND)

    task_factory(
        day_id=day.id,
        category=TaskCategory.MONEY,
        is_bonus=True,
    )

    assert day_service.is_day_ready(day) is False


def test_day_is_not_ready_with_more_than_required_core_tasks(
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(required_core_tasks=5)

    task_factory(day_id=day.id, category=TaskCategory.MIND)
    task_factory(day_id=day.id, category=TaskCategory.BODY)
    task_factory(day_id=day.id, category=TaskCategory.MONEY)
    task_factory(day_id=day.id, category=TaskCategory.MIND)
    task_factory(day_id=day.id, category=TaskCategory.MONEY)
    task_factory(day_id=day.id, category=TaskCategory.BODY)

    assert day_service.is_day_ready(day) is False


def test_cannot_complete_task_when_day_is_not_ready(
    db_session: Session,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(required_core_tasks=5)

    task = task_factory(
        day_id=day.id,
        category=TaskCategory.MIND,
    )

    with pytest.raises(DayNotReadyError):
        day_service.complete_task(
            db_session,
            task_id=task.id,
        )


def test_can_complete_task_when_day_is_ready(
    db_session: Session,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(required_core_tasks=5)

    task = task_factory(
        day_id=day.id,
        category=TaskCategory.MIND,
    )
    task_factory(day_id=day.id, category=TaskCategory.BODY)
    task_factory(day_id=day.id, category=TaskCategory.MONEY)
    task_factory(day_id=day.id, category=TaskCategory.MIND)
    task_factory(day_id=day.id, category=TaskCategory.MONEY)

    completed_task = day_service.complete_task(
        db_session,
        task_id=task.id,
    )

    assert completed_task.is_completed is True
    assert day.is_won is False


def test_completing_non_last_core_task_does_not_win_day(
    db_session: Session,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(required_core_tasks=5)

    task = task_factory(
        day_id=day.id,
        category=TaskCategory.MIND,
    )
    task_factory(
        day_id=day.id,
        category=TaskCategory.BODY,
        is_completed=True,
    )
    task_factory(
        day_id=day.id,
        category=TaskCategory.MONEY,
        is_completed=True,
    )
    task_factory(
        day_id=day.id,
        category=TaskCategory.MIND,
        is_completed=True,
    )
    task_factory(
        day_id=day.id,
        category=TaskCategory.MONEY,
        is_completed=False,
    )

    day_service.complete_task(
        db_session,
        task_id=task.id,
    )

    assert day.is_won is False


def test_completing_last_core_task_wins_day(
    db_session: Session,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(required_core_tasks=5)

    task_factory(
        day_id=day.id,
        category=TaskCategory.MIND,
        is_completed=True,
    )
    task_factory(
        day_id=day.id,
        category=TaskCategory.BODY,
        is_completed=True,
    )
    task_factory(
        day_id=day.id,
        category=TaskCategory.MONEY,
        is_completed=True,
    )
    task_factory(
        day_id=day.id,
        category=TaskCategory.MIND,
        is_completed=True,
    )
    last_task = task_factory(
        day_id=day.id,
        category=TaskCategory.MONEY,
        is_completed=False,
    )

    day_service.complete_task(
        db_session,
        task_id=last_task.id,
    )

    assert last_task.is_completed is True
    assert day.is_won is True


def test_cannot_complete_core_task_after_day_is_won(
    db_session: Session,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(
        required_core_tasks=5,
        is_won=True,
    )

    task = task_factory(
        day_id=day.id,
        category=TaskCategory.MIND,
        is_completed=False,
    )
    task_factory(
        day_id=day.id,
        category=TaskCategory.BODY,
        is_completed=True,
    )
    task_factory(
        day_id=day.id,
        category=TaskCategory.MONEY,
        is_completed=True,
    )
    task_factory(
        day_id=day.id,
        category=TaskCategory.MIND,
        is_completed=True,
    )
    task_factory(
        day_id=day.id,
        category=TaskCategory.MONEY,
        is_completed=True,
    )

    with pytest.raises(DayAlreadyWonError):
        day_service.complete_task(
            db_session,
            task_id=task.id,
        )


def test_bonus_task_does_not_affect_day_win(
    db_session: Session,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(
        required_core_tasks=5,
        is_won=True,
    )

    bonus_task = task_factory(
        day_id=day.id,
        category=TaskCategory.MIND,
        is_bonus=True,
        is_completed=False,
    )

    completed_task = day_service.complete_task(
        db_session,
        task_id=bonus_task.id,
    )

    assert completed_task.is_completed is True
    assert day.is_won is True


def test_cannot_complete_backlog_task(
    db_session: Session,
    task_factory: TaskFactory,
) -> None:
    task = task_factory(
        day_id=None,
    )

    with pytest.raises(TaskNotAssignedToDayError):
        day_service.complete_task(
            db_session,
            task_id=task.id,
        )


def test_complete_nonexistent_task_raises_error(
    db_session: Session,
) -> None:
    with pytest.raises(TaskNotFoundError):
        day_service.complete_task(
            db_session,
            task_id=999,
        )


def test_uncomplete_core_task(
    db_session: Session,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory()

    task = task_factory(
        day_id=day.id,
        is_completed=True,
    )

    uncompleted_task = day_service.uncomplete_task(
        db_session,
        task_id=task.id,
    )

    assert uncompleted_task.is_completed is False


def test_uncomplete_already_uncompleted_task_is_idempotent(
    db_session: Session,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory()

    task = task_factory(
        day_id=day.id,
        is_completed=False,
    )

    uncompleted_task = day_service.uncomplete_task(
        db_session,
        task_id=task.id,
    )

    assert uncompleted_task.is_completed is False


def test_cannot_uncomplete_core_task_after_day_is_won(
    db_session: Session,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(is_won=True)

    task = task_factory(
        day_id=day.id,
        is_completed=True,
        is_bonus=False,
    )

    with pytest.raises(DayAlreadyWonError):
        day_service.uncomplete_task(
            db_session,
            task_id=task.id,
        )


def test_can_uncomplete_bonus_task_after_day_is_won(
    db_session: Session,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(is_won=True)

    task = task_factory(
        day_id=day.id,
        is_completed=True,
        is_bonus=True,
    )

    uncompleted_task = day_service.uncomplete_task(
        db_session,
        task_id=task.id,
    )

    assert uncompleted_task.is_completed is False


def test_cannot_uncomplete_backlog_task(
    db_session: Session,
    task_factory: TaskFactory,
) -> None:
    task = task_factory(
        day_id=None,
        is_completed=True,
    )

    with pytest.raises(TaskNotAssignedToDayError):
        day_service.uncomplete_task(
            db_session,
            task_id=task.id,
        )


def test_uncomplete_nonexistent_task_raises_error(
    db_session: Session,
) -> None:
    with pytest.raises(TaskNotFoundError):
        day_service.uncomplete_task(
            db_session,
            task_id=999,
        )


def test_assign_task_to_day_as_core_task_before_day_is_won(
    db_session: Session,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(
        required_core_tasks=5,
        is_won=False,
    )
    task = task_factory(
        day_id=None,
        is_bonus=False,
    )

    assigned_task = day_service.assign_task_to_day(
        db_session,
        day_id=day.id,
        task_id=task.id,
    )

    assert assigned_task.day_id == day.id
    assert assigned_task.is_bonus is False


def test_assign_task_to_won_day_as_bonus(
    db_session: Session,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(
        is_won=True,
    )
    task = task_factory(
        day_id=None,
        is_bonus=False,
    )

    assigned_task = day_service.assign_task_to_day(
        db_session,
        day_id=day.id,
        task_id=task.id,
    )

    assert assigned_task.day_id == day.id
    assert assigned_task.is_bonus is True


def test_cannot_assign_more_than_required_core_tasks(
    db_session: Session,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(
        required_core_tasks=5,
        is_won=False,
    )

    task_factory(day_id=day.id)
    task_factory(day_id=day.id)
    task_factory(day_id=day.id)
    task_factory(day_id=day.id)
    task_factory(day_id=day.id)

    backlog_task = task_factory(
        day_id=None,
    )

    with pytest.raises(CoreTaskLimitReachedError):
        day_service.assign_task_to_day(
            db_session,
            day_id=day.id,
            task_id=backlog_task.id,
        )


def test_assign_task_to_same_full_day_is_idempotent(
    db_session: Session,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(
        required_core_tasks=5,
        is_won=False,
    )

    task = task_factory(day_id=day.id)
    task_factory(day_id=day.id)
    task_factory(day_id=day.id)
    task_factory(day_id=day.id)
    task_factory(day_id=day.id)

    assigned_task = day_service.assign_task_to_day(
        db_session,
        day_id=day.id,
        task_id=task.id,
    )

    assert assigned_task.day_id == day.id
    assert assigned_task.is_bonus is False


def test_create_task_for_day_creates_core_task_before_win(
    db_session: Session,
    day_factory: DayFactory,
) -> None:
    day = day_factory(
        is_won=False,
    )

    task = day_service.create_task_for_day(
        db_session,
        day_id=day.id,
        task_data=TaskCreate(
            title="Practice bass",
            category=TaskCategory.MIND,
            estimated_minutes=30,
        ),
    )

    assert task.day_id == day.id
    assert task.is_bonus is False


def test_create_task_for_won_day_creates_bonus_task(
    db_session: Session,
    day_factory: DayFactory,
) -> None:
    day = day_factory(
        is_won=True,
    )

    task = day_service.create_task_for_day(
        db_session,
        day_id=day.id,
        task_data=TaskCreate(
            title="Practice bass",
            category=TaskCategory.MIND,
            estimated_minutes=30,
        ),
    )

    assert task.day_id == day.id
    assert task.is_bonus is True


def test_cannot_create_more_than_required_core_tasks(
    db_session: Session,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(
        required_core_tasks=5,
        is_won=False,
    )

    for _ in range(5):
        task_factory(day_id=day.id)

    with pytest.raises(CoreTaskLimitReachedError):
        day_service.create_task_for_day(
            db_session,
            day_id=day.id,
            task_data=TaskCreate(
                title="One task too many",
                category=TaskCategory.MIND,
                estimated_minutes=30,
            ),
        )


def test_assign_bonus_task_to_unwon_day_resets_is_bonus(
    db_session: Session,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    source_day = day_factory(
        day_date=date(2026, 9, 13),
        is_won=True,
    )
    target_day = day_factory(
        day_date=date(2026, 9, 14),
        is_won=False,
    )

    task = task_factory(
        day_id=source_day.id,
        is_bonus=True,
    )

    assigned_task = day_service.assign_task_to_day(
        db_session,
        day_id=target_day.id,
        task_id=task.id,
    )

    assert assigned_task.day_id == target_day.id
    assert assigned_task.is_bonus is False


def test_unassign_task_resets_is_bonus(
    db_session: Session,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(is_won=True)

    task = task_factory(
        day_id=day.id,
        is_bonus=True,
    )

    unassigned_task = day_service.unassign_task_from_day(
        db_session,
        day_id=day.id,
        task_id=task.id,
    )

    assert unassigned_task.day_id is None
    assert unassigned_task.is_bonus is False


def test_cannot_unassign_core_task_from_won_day(
    db_session: Session,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(is_won=True)

    task = task_factory(
        day_id=day.id,
        is_bonus=False,
    )

    with pytest.raises(DayAlreadyWonError):
        day_service.unassign_task_from_day(
            db_session,
            day_id=day.id,
            task_id=task.id,
        )


def test_can_unassign_bonus_task_from_won_day(
    db_session: Session,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(is_won=True)

    task = task_factory(
        day_id=day.id,
        is_bonus=True,
    )

    unassigned_task = day_service.unassign_task_from_day(
        db_session,
        day_id=day.id,
        task_id=task.id,
    )

    assert unassigned_task.day_id is None
    assert unassigned_task.is_bonus is False


def test_cannot_move_core_task_from_won_day(
    db_session: Session,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    source_day = day_factory(
        day_date=date(2026, 9, 13),
        is_won=True,
    )
    target_day = day_factory(
        day_date=date(2026, 9, 14),
        is_won=False,
    )

    task = task_factory(
        day_id=source_day.id,
        is_bonus=False,
    )

    with pytest.raises(DayAlreadyWonError):
        day_service.assign_task_to_day(
            db_session,
            day_id=target_day.id,
            task_id=task.id,
        )


def test_can_move_bonus_task_from_won_day(
    db_session: Session,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    source_day = day_factory(
        day_date=date(2026, 9, 13),
        is_won=True,
    )
    target_day = day_factory(
        day_date=date(2026, 9, 14),
        is_won=False,
    )

    task = task_factory(
        day_id=source_day.id,
        is_bonus=True,
    )

    assigned_task = day_service.assign_task_to_day(
        db_session,
        day_id=target_day.id,
        task_id=task.id,
    )

    assert assigned_task.day_id == target_day.id
    assert assigned_task.is_bonus is False


def test_complete_already_completed_core_task_is_idempotent(
    db_session: Session,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(
        required_core_tasks=5,
        is_won=False,
    )

    task = task_factory(
        day_id=day.id,
        category=TaskCategory.MIND,
        is_completed=True,
    )
    task_factory(
        day_id=day.id,
        category=TaskCategory.BODY,
        is_completed=False,
    )
    task_factory(
        day_id=day.id,
        category=TaskCategory.MONEY,
        is_completed=False,
    )
    task_factory(
        day_id=day.id,
        category=TaskCategory.MIND,
        is_completed=False,
    )
    task_factory(
        day_id=day.id,
        category=TaskCategory.MONEY,
        is_completed=False,
    )

    completed_task = day_service.complete_task(
        db_session,
        task_id=task.id,
    )

    assert completed_task.is_completed is True
    assert day.is_won is False


def test_complete_already_completed_core_task_after_win_is_idempotent(
    db_session: Session,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(
        is_won=True,
    )

    task = task_factory(
        day_id=day.id,
        is_bonus=False,
        is_completed=True,
    )

    completed_task = day_service.complete_task(
        db_session,
        task_id=task.id,
    )

    assert completed_task.is_completed is True
    assert day.is_won is True


def test_complete_already_completed_bonus_task_is_idempotent(
    db_session: Session,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(is_won=True)

    task = task_factory(
        day_id=day.id,
        is_bonus=True,
        is_completed=True,
    )

    completed_task = day_service.complete_task(
        db_session,
        task_id=task.id,
    )

    assert completed_task.is_completed is True
    assert day.is_won is True


def test_uncomplete_already_uncompleted_core_task_is_idempotent(
    db_session: Session,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(is_won=False)

    task = task_factory(
        day_id=day.id,
        is_bonus=False,
        is_completed=False,
    )

    uncompleted_task = day_service.uncomplete_task(
        db_session,
        task_id=task.id,
    )

    assert uncompleted_task.is_completed is False


def test_uncomplete_already_uncompleted_bonus_task_is_idempotent(
    db_session: Session,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(is_won=True)

    task = task_factory(
        day_id=day.id,
        is_bonus=True,
        is_completed=False,
    )

    uncompleted_task = day_service.uncomplete_task(
        db_session,
        task_id=task.id,
    )

    assert uncompleted_task.is_completed is False
    assert day.is_won is True


def test_assign_task_to_same_day_is_idempotent_when_day_is_full(
    db_session: Session,
    day_factory: DayFactory,
    task_factory: TaskFactory,
) -> None:
    day = day_factory(
        required_core_tasks=5,
        is_won=False,
    )

    task = task_factory(day_id=day.id)
    task_factory(day_id=day.id)
    task_factory(day_id=day.id)
    task_factory(day_id=day.id)
    task_factory(day_id=day.id)

    assigned_task = day_service.assign_task_to_day(
        db_session,
        day_id=day.id,
        task_id=task.id,
    )

    assert assigned_task.id == task.id
    assert assigned_task.day_id == day.id