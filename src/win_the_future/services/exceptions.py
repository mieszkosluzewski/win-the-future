class DomainError(Exception):
    pass


class DayNotFoundError(DomainError):
    pass


class TaskNotFoundError(DomainError):
    pass


class TaskNotAssignedToDayError(DomainError):
    pass


class DayNotReadyError(DomainError):
    pass


class DayAlreadyWonError(DomainError):
    pass


class InvalidBonusTaskError(DomainError):
    pass


class CoreTaskLimitReachedError(DomainError):
    pass

class DayNotCurrentError(DomainError):
    pass
