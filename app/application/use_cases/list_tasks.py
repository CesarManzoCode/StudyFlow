from datetime import datetime

from app.application.services.task_priority_service import TaskPriorityService
from app.domain.models.task import PrioritizedTask
from app.domain.ports.task_repository import TaskRepository


class ListTasksUseCase:
    """
    Return the current pending task snapshot prioritized by urgency.
    """

    def __init__(
        self,
        task_repository: TaskRepository,
        task_priority_service: TaskPriorityService,
    ) -> None:
        self._task_repository = task_repository
        self._task_priority_service = task_priority_service

    async def execute(self, now: datetime) -> list[PrioritizedTask]:
        """
        Load pending tasks from the repository, prioritize them, and return them
        ordered from most urgent to least urgent.
        """
        pending_tasks = await self._task_repository.list_pending()
        return self._task_priority_service.prioritize_many(tasks=pending_tasks, now=now)