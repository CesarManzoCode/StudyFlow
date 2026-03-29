from datetime import datetime

from app.application.services.day_planning_service import DayPlaningService
from app.application.services.task_priority_service import TaskPriorityService
from app.domain.models.day_plan import DayPlan
from app.domain.ports.task_repository import TaskRepository


class PlanDayUseCase:
    """
    Orchestrate the daily planning workflow:
    1. Fetch pending tasks from repository
    2. Prioritize using TaskPriorityService
    3. Plan the day using DayPlaningService
    """

    def __init__(
        self,
        task_repository: TaskRepository,
        task_priority_service: TaskPriorityService,
        day_planning_service: DayPlaningService,
    ) -> None:
        self._task_repository = task_repository
        self._task_priority_service = task_priority_service
        self._day_planning_service = day_planning_service

    async def execute(self, now: datetime | None = None) -> DayPlan:
        """
        Generate a day plan for today.

        Returns:
            DayPlan with ordered tasks and time allocations
        """
        now = now or datetime.utcnow()

        # 1. Fetch pending tasks
        pending_tasks = await self._task_repository.list_pending()

        # 2. Prioritize
        prioritized_tasks = self._task_priority_service.prioritize_many(
            pending_tasks, now
        )

        # 3. Plan the day
        day_plan = await self._day_planning_service.plan_day(
            prioritized_tasks, now
        )

        return day_plan
