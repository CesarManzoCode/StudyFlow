from datetime import datetime, timedelta
import logging

from app.domain.enums import TaskPriority
from app.domain.models.day_plan import (
    CognitiveLoad,
    DayPlan,
    EstimatedTaskSize,
    PlannedTask,
    TaskDifficulty,
)
from app.domain.models.task import PrioritizedTask, Task
from app.domain.models.task_step import StepDifficulty, TaskStep
from app.domain.ports.llm_client import LlmClient


logger = logging.getLogger(__name__)


class DayPlaningService:
    """
    Orchestrate daily task planning with time estimation, difficulty assessment,
    and cognitive load pacing.

    This service transforms a prioritized task list into a scheduled day plan
    that balances urgency (deadline) with cognitive feasibility (effort + pacing).
    """

    def __init__(self, llm_client: LlmClient | None = None) -> None:
        self._llm_client = llm_client

    async def plan_day(
        self,
        prioritized_tasks: list[PrioritizedTask],
        now: datetime,
        max_minutes: int = 480,  # 8 hours
    ) -> DayPlan:
        """
        Create a day plan from prioritized tasks.

        Args:
            prioritized_tasks: Tasks already sorted by priority (from TaskPriorityService)
            now: Current datetime
            max_minutes: Maximum time budget for the day (default 8 hours)

        Returns:
            DayPlan with ordered task sequence
        """
        # Filter to tasks that should be done today (critical + high + medium priority)
        today_candidates = [
            pt for pt in prioritized_tasks
            if pt.priority in {TaskPriority.CRITICAL, TaskPriority.HIGH, TaskPriority.MEDIUM}
        ]

        # Estimate time and difficulty for each candidate
        estimated_tasks = []
        for prioritized_task in today_candidates:
            estimated_tasks.append(
                await self._estimate_task(prioritized_task)
            )

        # Sort by priority + deadline, then apply cognitive pacing
        sorted_tasks = self._sort_by_cognitive_pacing(estimated_tasks)

        # Allocate to fit within max_minutes
        allocated_tasks = self._allocate_to_time_budget(
            sorted_tasks, max_minutes
        )

        # Create day plan
        plan = DayPlan(
            created_at=now,
            planned_for_date=now.replace(hour=0, minute=0, second=0, microsecond=0),
            planned_tasks=allocated_tasks,
            total_estimated_minutes=sum(t.estimated_minutes for t in allocated_tasks),
            pending_tasks_count=len(prioritized_tasks) - len(allocated_tasks),
        )

        return plan

    async def _estimate_task(self, prioritized_task: PrioritizedTask) -> PlannedTask:
        """
        Estimate time, size, difficulty, and cognitive load for a task.
        """
        task = prioritized_task.task

        llm_estimation = await self._estimate_from_llm(task)
        if llm_estimation is not None:
            estimated_minutes, difficulty = llm_estimation
            cognitive_load = self._infer_cognitive_load(difficulty)
        else:
            # Start with reasonable defaults when LLM estimation is unavailable.
            estimated_minutes = self._estimate_minutes_from_description(task.description_text or "")
            difficulty = self._infer_difficulty_from_description(task.description_text or "")
            cognitive_load = self._infer_cognitive_load(difficulty)

        size = self._minutes_to_size(estimated_minutes)

        return PlannedTask(
            task=prioritized_task,
            estimated_minutes=estimated_minutes,
            size=size,
            difficulty=difficulty,
            cognitive_load=cognitive_load,
        )

    async def _estimate_from_llm(
        self,
        task: Task,
    ) -> tuple[int, TaskDifficulty] | None:
        """
        Try to estimate task effort from the LLM enhanced checklist output.

        Returns None when provider data is unavailable so caller can fallback
        to deterministic local heuristics.
        """
        if self._llm_client is None:
            return None

        try:
            enhanced = await self._llm_client.generate_enhanced_checklist(task=task)
        except Exception as exc:
            logger.warning("LLM estimation failed for task %s: %s", task.id, exc)
            return None

        if not enhanced.steps:
            return None

        raw_minutes = sum(step.estimated_minutes for step in enhanced.steps)
        clamped_minutes = max(15, min(240, raw_minutes))

        mapped_difficulty = self._map_step_difficulties_to_task(enhanced.steps)
        return clamped_minutes, mapped_difficulty

    def _map_step_difficulties_to_task(self, steps: list[TaskStep]) -> TaskDifficulty:
        """Map max step difficulty to task-level difficulty."""
        level_map = {
            StepDifficulty.TRIVIAL: 0,
            StepDifficulty.EASY: 1,
            StepDifficulty.MODERATE: 2,
            StepDifficulty.HARD: 3,
        }
        max_level = max((level_map.get(step.difficulty, 2) for step in steps), default=2)

        if max_level >= 3:
            return TaskDifficulty.HARD
        if max_level <= 1:
            return TaskDifficulty.EASY
        return TaskDifficulty.MODERATE

    def _estimate_minutes_from_description(self, description: str) -> int:
        """
        Heuristic time estimation based on description keywords.
        """
        description_lower = description.lower()

        # Keywords for different durations
        short_keywords = ["write", "review", "check", "read", "edit"]
        medium_keywords = ["create", "design", "analyze", "research", "implement"]
        long_keywords = ["develop", "comprehensive", "project", "build", "system"]

        for kw in long_keywords:
            if kw in description_lower:
                return 120  # 2 hours

        for kw in medium_keywords:
            if kw in description_lower:
                return 60  # 1 hour

        for kw in short_keywords:
            if kw in description_lower:
                return 30  # 30 min

        # Default for unclear descriptions
        return 45  # 45 min

    def _infer_difficulty_from_description(self, description: str) -> TaskDifficulty:
        """
        Infer difficulty from description keywords.
        """
        description_lower = description.lower()

        hard_keywords = ["complex", "difficult", "advanced", "challenging", "critical"]
        easy_keywords = ["simple", "basic", "easy", "straightforward", "routine"]

        for kw in hard_keywords:
            if kw in description_lower:
                return TaskDifficulty.HARD

        for kw in easy_keywords:
            if kw in description_lower:
                return TaskDifficulty.EASY

        return TaskDifficulty.MODERATE

    def _infer_cognitive_load(self, difficulty: TaskDifficulty) -> CognitiveLoad:
        """
        Map difficulty to cognitive load.
        """
        if difficulty == TaskDifficulty.HARD:
            return CognitiveLoad.HEAVY
        elif difficulty == TaskDifficulty.EASY:
            return CognitiveLoad.LIGHT
        else:
            return CognitiveLoad.MODERATE

    def _minutes_to_size(self, minutes: int) -> EstimatedTaskSize:
        """Convert minutes to EstimatedTaskSize category."""
        if minutes <= 30:
            return EstimatedTaskSize.SHORT
        elif minutes >= 90:
            return EstimatedTaskSize.LONG
        else:
            return EstimatedTaskSize.MEDIUM

    def _sort_by_cognitive_pacing(
        self, tasks: list[PlannedTask]
    ) -> list[PlannedTask]:
        """
        Sort tasks by urgency, then apply cognitive pacing.

        Strategy:
        1. Place CRITICAL tasks (deadlines matter most)
        2. Alternate HEAVY/LIGHT cognitive loads for better endurance
        3. Place MEDIUM/HIGH priority tasks
        """
        def get_priority(planned_task: PlannedTask) -> TaskPriority:
            """Extract priority from PlannedTask."""
            if isinstance(planned_task.task, PrioritizedTask):
                return planned_task.task.priority
            # For regular Task, use NONE as default
            return TaskPriority.NONE
        
        def get_task_id(planned_task: PlannedTask) -> str:
            """Extract task ID from PlannedTask."""
            if isinstance(planned_task.task, PrioritizedTask):
                return planned_task.task.task.id
            return planned_task.task.id
        
        def get_due_at(planned_task: PlannedTask):
            """Extract due_at from PlannedTask."""
            if isinstance(planned_task.task, PrioritizedTask):
                return planned_task.task.task.due_at or datetime.max
            return planned_task.task.due_at or datetime.max
        
        critical_tasks = [t for t in tasks if get_priority(t) == TaskPriority.CRITICAL]
        high_tasks = [t for t in tasks if get_priority(t) == TaskPriority.HIGH]
        medium_tasks = [t for t in tasks if get_priority(t) == TaskPriority.MEDIUM]

        # Sort each group by deadline
        critical_tasks.sort(
            key=lambda t: (
                get_due_at(t),
                t.difficulty.value,
            )
        )
        high_tasks.sort(
            key=lambda t: (
                get_due_at(t),
                t.difficulty.value,
            )
        )
        medium_tasks.sort(
            key=lambda t: (
                get_due_at(t),
                t.difficulty.value,
            )
        )

        # Merge with cognitive pacing: alternate heavy/light
        result = []
        last_load = None

        for task in critical_tasks + high_tasks + medium_tasks:
            # If last task was heavy, try to pick a light one
            if last_load == CognitiveLoad.HEAVY and any(
                t.cognitive_load == CognitiveLoad.LIGHT and t not in result
                for t in tasks
            ):
                light_task = next(
                    (t for t in tasks
                     if t.cognitive_load == CognitiveLoad.LIGHT and t not in result),
                    task,
                )
                result.append(light_task)
                last_load = light_task.cognitive_load
            else:
                result.append(task)
                last_load = task.cognitive_load

        # Remove duplicates while preserving order
        seen = set()
        unique_result = []
        for task in result:
            task_id = get_task_id(task)
            if task_id not in seen:
                unique_result.append(task)
                seen.add(task_id)

        return unique_result

    def _allocate_to_time_budget(
        self, tasks: list[PlannedTask], max_minutes: int
    ) -> list[PlannedTask]:
        """
        Allocate tasks that fit within time budget.
        """
        allocated = []
        total_minutes = 0

        for task in tasks:
            if total_minutes + task.estimated_minutes <= max_minutes:
                allocated.append(task)
                total_minutes += task.estimated_minutes

        return allocated
