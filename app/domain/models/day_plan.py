from datetime import datetime, timedelta
from enum import Enum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models.task import PrioritizedTask, Task


class EstimatedTaskSize(str, Enum):
    """Enum for estimated task sizes."""

    SHORT = "short"  # < 30 min
    MEDIUM = "medium"  # 30 - 90 min
    LONG = "long"  # > 90 min


class TaskDifficulty(str, Enum):
    """Enum for estimated task difficulty."""

    EASY = "easy"
    MODERATE = "moderate"
    HARD = "hard"


class CognitiveLoad(str, Enum):
    """Enum for cognitive load level."""

    LIGHT = "light"  # Routine, familiar work
    MODERATE = "moderate"  # Mixed complexity
    HEAVY = "heavy"  # Requires deep focus


class PlannedTask(BaseModel):
    """
    A task scheduled in the day plan with time allocation and difficulty info.
    """

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
    )

    task: PrioritizedTask | Task

    # Time estimation
    estimated_minutes: int = Field(..., ge=15, le=240, description="Estimated time in minutes")
    size: EstimatedTaskSize = Field(default=EstimatedTaskSize.MEDIUM)

    # Difficulty & cognitive load (v2 features)
    difficulty: TaskDifficulty = Field(default=TaskDifficulty.MODERATE)
    cognitive_load: CognitiveLoad = Field(default=CognitiveLoad.MODERATE)

    # Scheduling info
    scheduled_at: datetime | None = None
    sequence_position: int | None = None  # Order in the day plan

    @property
    def formatted_time_block(self) -> str:
        """Return formatted time block (e.g., '40 min')."""
        return f"{self.estimated_minutes} min"

    @property
    def hour_decimal(self) -> float:
        """Return estimated hours as decimal (e.g., 0.67 for 40 min)."""
        return self.estimated_minutes / 60.0


class DayPlan(BaseModel):
    """
    A plan for the day: ordered sequence of tasks with time blocks.

    This model represents the output of the planning algorithm - a
    recommended schedule optimized for deadline urgency and cognitive pacing.
    """

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
    )

    created_at: datetime
    planned_for_date: datetime  # Date the plan is for

    planned_tasks: list[PlannedTask] = Field(
        default_factory=list,
        description="Tasks ordered by recommended execution sequence",
    )

    total_estimated_minutes: int = Field(default=0)
    pending_tasks_count: int = Field(default=0)  # Tasks not included in today's plan

    @property
    def total_hours(self) -> float:
        """Return total estimated hours."""
        return self.total_estimated_minutes / 60.0

    @property
    def is_feasible(self) -> bool:
        """Check if plan fits in a reasonable workday (8 hours)."""
        return self.total_minutes <= (8 * 60)

    @property
    def total_minutes(self) -> int:
        """Return total minutes (same as total_estimated_minutes for convenience)."""
        return self.total_estimated_minutes

    @property
    def cognitive_balance(self) -> str:
        """Assess if the plan is cognitively balanced."""
        heavy_count = sum(
            1 for task in self.planned_tasks 
            if task.cognitive_load == CognitiveLoad.HEAVY
        )
        light_count = sum(
            1 for task in self.planned_tasks 
            if task.cognitive_load == CognitiveLoad.LIGHT
        )

        # Good balance: alternating light/heavy or mostly moderate
        if heavy_count <= 2 or light_count > 0:
            return "balanced"
        return "heavy"  # Too many heavy tasks in a row

    def with_planned_tasks(self, tasks: list[PlannedTask]) -> Self:
        """Return a new DayPlan with updated tasks."""
        total_minutes = sum(task.estimated_minutes for task in tasks)
        return self.model_copy(
            update={
                "planned_tasks": tasks,
                "total_estimated_minutes": total_minutes,
            }
        )
