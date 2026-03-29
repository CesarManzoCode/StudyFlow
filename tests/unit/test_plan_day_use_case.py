"""
Unit tests for PlanDayUseCase.
"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.application.use_cases.plan_day import PlanDayUseCase
from app.domain.enums import TaskPriority, TaskStatus
from app.domain.models.task import PrioritizedTask, Task


class TestPlanDayUseCase:
    """Test PlanDayUseCase."""

    @pytest.mark.asyncio
    async def test_plan_day_no_pending_tasks(self) -> None:
        """Should return empty plan when no pending tasks."""
        # Mock repositories and services
        task_repo = AsyncMock()
        task_repo.list_pending.return_value = []

        task_priority_service = AsyncMock()
        day_planning_service = AsyncMock()

        use_case = PlanDayUseCase(
            task_repository=task_repo,
            task_priority_service=task_priority_service,
            day_planning_service=day_planning_service,
        )

        plan = await use_case.execute()

        assert plan is not None
        task_repo.list_pending.assert_called_once()

    @pytest.mark.asyncio
    async def test_plan_day_fetches_pending_tasks(self) -> None:
        """Should fetch pending tasks from repository."""
        # Create mock task
        task = Task(
            id="task-1",
            course_name="Test",
            title="Assignment",
            status=TaskStatus.PENDING,
            url="http://example.com",
        )

        # Setup mocks
        task_repo = AsyncMock()
        task_repo.list_pending.return_value = [task]

        task_priority_service = AsyncMock()
        prioritized_task = PrioritizedTask(task=task, priority=TaskPriority.CRITICAL)
        task_priority_service.prioritize_many.return_value = [prioritized_task]

        day_planning_service = AsyncMock()
        day_planning_mock = AsyncMock()
        day_planning_service.plan_day.return_value = day_planning_mock

        use_case = PlanDayUseCase(
            task_repository=task_repo,
            task_priority_service=task_priority_service,
            day_planning_service=day_planning_service,
        )

        now = datetime.utcnow()
        plan = await use_case.execute(now)

        # Verify the chain was called
        task_repo.list_pending.assert_called_once()
        task_priority_service.prioritize_many.assert_called_once()
        day_planning_service.plan_day.assert_called_once()

    @pytest.mark.asyncio
    async def test_plan_day_uses_current_time(self) -> None:
        """Should use provided time or default to now."""
        task_repo = AsyncMock()
        task_repo.list_pending.return_value = []

        task_priority_service = AsyncMock()
        task_priority_service.prioritize_many.return_value = []

        day_planning_service = AsyncMock()
        day_planning_mock = AsyncMock()
        day_planning_service.plan_day.return_value = day_planning_mock

        use_case = PlanDayUseCase(
            task_repository=task_repo,
            task_priority_service=task_priority_service,
            day_planning_service=day_planning_service,
        )

        # Use specific time
        now = datetime(2026, 3, 28, 10, 0, 0)
        plan = await use_case.execute(now)

        # Verify time was passed to day_planning_service
        call_args = day_planning_service.plan_day.call_args
        assert call_args[0][1] == now  # Second arg is the datetime
