class DomainError(Exception):
    pass


class DayNotFoundError(DomainError):
    pass


class TaskNotFoundError(DomainError):
    pass


class TaskNotAssignedToDayError(DomainError):
    pass
