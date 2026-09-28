from collections.abc import Callable

from win_the_future.models import Day, Task, User

TaskFactory = Callable[..., Task]
DayFactory = Callable[..., Day]
UserFactory = Callable[..., User]


def make_task_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "title": "Test task",
        "category": "mind",
        "estimated_minutes": 30,
    }

    return payload | overrides
