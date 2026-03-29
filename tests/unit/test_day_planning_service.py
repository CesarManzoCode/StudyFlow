"""
Unit tests for day planning service.
"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.application.services.day_planning_service import DayPlaningService
from app.domain.enums import TaskPriority, TaskStatus
from app.domain.models.day_plan import (
    CognitiveLoad,
    EstimatedTaskSize,
    PlannedTask,
    TaskDifficulty,
)
from app.domain.models.task import PrioritizedTask, Task


def _get_task_id(planned_task: PlannedTask) -> str:
    """Extract task ID from PlannedTask."""
    if isinstance(planned_task.task, PrioritizedTask):
        return planned_task.task.task.id
    return planned_task.task.id


class TestDayPlaningService:
    """Test DayPlaningService."""

    def create_test_task(
        self,
        task_id: str,
        title: str,
        description: str,
        priority: TaskPriority,
        due_at: datetime | None = None,
    ) -> PrioritizedTask:
        """Helper to create a test PrioritizedTask."""
        task = Task(
            id=task_id,
            course_name="Test Course",
            title=title,
            description_text=description,
            due_at=due_at,
            status=TaskStatus.PENDING,
            url="http://example.com",
        )
        return PrioritizedTask(task=task, priority=priority)

    @pytest.mark.asyncio
    async def test_plan_day_empty_tasks(self) -> None:
        """Should handle empty task list."""
        service = DayPlaningService()
        now = datetime.utcnow()

        plan = await service.plan_day([], now)

        assert len(plan.planned_tasks) == 0
        assert plan.total_minutes == 0
        assert plan.is_feasible

    @pytest.mark.asyncio
    async def test_plan_day_critical_task(self) -> None:
        """Should include critical tasks."""
        service = DayPlaningService()
        now = datetime.utcnow()

        task = self.create_test_task(
            "task-1",
            "Critical Assignment",
            "Analyze the research paper",
            TaskPriority.CRITICAL,
            due_at=now,
        )

        plan = await service.plan_day([task], now)

        assert len(plan.planned_tasks) == 1
        assert _get_task_id(plan.planned_tasks[0]) == "task-1"

    @pytest.mark.asyncio
    async def test_plan_day_respects_time_budget(self) -> None:
        """Should not exceed time budget."""
        service = DayPlaningService()
        now = datetime.utcnow()

        tasks = [
            self.create_test_task(
                f"task-{i}",
                f"Task {i}",
                f"Create something (medium task)",
                TaskPriority.CRITICAL,
                due_at=now,
            )
            for i in range(10)  # Each will be ~60 min by default
        ]

        max_minutes = 120  # 2 hours
        plan = await service.plan_day(tasks, now, max_minutes)

        assert plan.total_minutes <= max_minutes
        assert len(plan.planned_tasks) <= len(tasks)

    @pytest.mark.asyncio
    async def test_estimate_task_short_description(self) -> None:
        """Should estimate short tasks correctly."""
        service = DayPlaningService()

        task = Task(
            id="task-1",
            course_name="Test",
            title="Review",
            description_text="Review the requirements",
            status=TaskStatus.PENDING,
            url="http://example.com",
        )
        prioritized_task = PrioritizedTask(task=task, priority=TaskPriority.MEDIUM)

        estimated = await service._estimate_task(prioritized_task)

        assert estimated.estimated_minutes < 45
        assert estimated.size == EstimatedTaskSize.SHORT

    @pytest.mark.asyncio
    async def test_estimate_task_long_description(self) -> None:
        """Should estimate long tasks correctly."""
        service = DayPlaningService()

        task = Task(
            id="task-1",
            course_name="Test",
            title="Develop",
            description_text="Develop a comprehensive system",
            status=TaskStatus.PENDING,
            url="http://example.com",
        )
        prioritized_task = PrioritizedTask(task=task, priority=TaskPriority.MEDIUM)

        estimated = await service._estimate_task(prioritized_task)

        assert estimated.estimated_minutes >= 90
        assert estimated.size == EstimatedTaskSize.LONG

    def test_infer_difficulty_hard(self) -> None:
        """Should identify hard tasks."""
        service = DayPlaningService()

        difficulty = service._infer_difficulty_from_description(
            "Implement a complex algorithm"
        )

        assert difficulty == TaskDifficulty.HARD

    def test_infer_difficulty_easy(self) -> None:
        """Should identify easy tasks."""
        service = DayPlaningService()

        difficulty = service._infer_difficulty_from_description(
            "Read the simple requirements"
        )

        assert difficulty == TaskDifficulty.EASY

    def test_infer_cognitive_load_from_difficulty(self) -> None:
        """Should map difficulty to cognitive load."""
        service = DayPlaningService()

        heavy_load = service._infer_cognitive_load(TaskDifficulty.HARD)
        light_load = service._infer_cognitive_load(TaskDifficulty.EASY)

        assert heavy_load == CognitiveLoad.HEAVY
        assert light_load == CognitiveLoad.LIGHT

    @pytest.mark.asyncio
    async def test_plan_day_cognitive_pacing(self) -> None:
        """Should pace heavy and light tasks throughout the day."""
        service = DayPlaningService()
        now = datetime.utcnow()

        # Mix of difficult and easy tasks
        tasks = [
            self.create_test_task(
                "hard-1",
                "Hard Task 1",
                "Develop a complex system",
                TaskPriority.CRITICAL,
                now,
            ),
            self.create_test_task(
                "easy-1",
                "Easy Task 1",
                "Review requirements",
                TaskPriority.CRITICAL,
                now,
            ),
            self.create_test_task(
                "hard-2",
                "Hard Task 2",
                "Implement advanced features",
                TaskPriority.HIGH,
                now,
            ),
        ]

        plan = await service.plan_day(tasks, now, max_minutes=300)

        # Should have both tasks
        assert len(plan.planned_tasks) >= 2

        # Check cognitive balance
        tasks_by_load = {}
        for task in plan.planned_tasks:
            load = task.cognitive_load
            tasks_by_load[load] = tasks_by_load.get(load, 0) + 1

        # Should not be all heavy
        assert CognitiveLoad.HEAVY not in tasks_by_load or tasks_by_load[CognitiveLoad.HEAVY] < len(
            plan.planned_tasks
        )

    def test_day_plan_is_feasible(self) -> None:
        """Should determination feasibility based on time budget."""
        from app.domain.models.day_plan import DayPlan

        # Feasible plan (4 hours)
        feasible_plan = DayPlan(
            created_at=datetime.utcnow(),
            planned_for_date=datetime.utcnow(),
            planned_tasks=[],
            total_estimated_minutes=240,
        )
        assert feasible_plan.is_feasible

        # Not feasible (12 hours)
        unfeasible_plan = DayPlan(
            created_at=datetime.utcnow(),
            planned_for_date=datetime.utcnow(),
            planned_tasks=[],
            total_estimated_minutes=720,
        )
        assert not unfeasible_plan.is_feasible

    def test_day_plan_cognitive_balance(self) -> None:
        """Should assess cognitive balance."""
        from app.domain.models.day_plan import DayPlan, PlannedTask

        task = Task(
            id="task-1",
            course_name="Test",
            title="Test",
            status=TaskStatus.PENDING,
            url="http://example.com",
        )

        # Plan with varied cognitive loads
        balanced_tasks = [
            PlannedTask(
                task=task,
                priority=TaskPriority.CRITICAL,
                estimated_minutes=60,
                cognitive_load=CognitiveLoad.HEAVY,
            ),
            PlannedTask(
                task=task,
                priority=TaskPriority.HIGH,
                estimated_minutes=30,
                cognitive_load=CognitiveLoad.LIGHT,
            ),
        ]

        plan = DayPlan(
            created_at=datetime.utcnow(),
            planned_for_date=datetime.utcnow(),
            planned_tasks=balanced_tasks,
            total_estimated_minutes=90,
        )

        assert plan.cognitive_balance == "balanced"
