"""
Routes for day planning (Plan My Day feature).
"""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.domain.enums import TaskPriority
from app.domain.models.day_plan import DayPlan, PlannedTask
from app.domain.models.task import PrioritizedTask
from app.infrastructure.factories import AppContainer


router = APIRouter(prefix="/api/plan", tags=["planning"])


def _get_container(request: Request) -> AppContainer:
    """Get the shared application container from app state."""
    return request.app.state.container


def _get_task_id(planned_task: PlannedTask) -> str:
    """Extract task ID from PlannedTask."""
    if isinstance(planned_task.task, PrioritizedTask):
        return planned_task.task.task.id
    return planned_task.task.id


def _get_course_name(planned_task: PlannedTask) -> str:
    """Extract course name from PlannedTask."""
    if isinstance(planned_task.task, PrioritizedTask):
        return planned_task.task.task.course_name
    return planned_task.task.course_name


def _get_title(planned_task: PlannedTask) -> str:
    """Extract title from PlannedTask."""
    if isinstance(planned_task.task, PrioritizedTask):
        return planned_task.task.task.title
    return planned_task.task.title


def _get_priority(planned_task: PlannedTask) -> TaskPriority:
    """Extract priority from PlannedTask."""
    if isinstance(planned_task.task, PrioritizedTask):
        return planned_task.task.priority
    return TaskPriority.NONE


# =========================================================
# REQUEST/RESPONSE MODELS
# =========================================================


class PlannedTaskResponse(BaseModel):
    """Response model for a planned task."""

    task_id: str
    course_name: str
    title: str
    priority: str
    estimated_minutes: int
    formatted_time_block: str
    difficulty: str
    cognitive_load: str
    sequence_position: int | None = None


class DayPlanResponse(BaseModel):
    """Response model for the day plan."""

    created_at: str
    planned_for_date: str
    planned_tasks: list[PlannedTaskResponse]
    total_minutes: int
    total_hours: float
    is_feasible: bool
    cognitive_balance: str
    pending_tasks_count: int


# =========================================================
# ENDPOINTS
# =========================================================


@router.get("/my-day", response_model=DayPlanResponse)
async def plan_my_day(
    container: AppContainer = Depends(_get_container),
) -> DayPlanResponse:
    """
    Generate an intelligent day plan for today.

    Returns:
        DayPlanResponse with ordered tasks and time allocations
    """
    # Execute use case
    day_plan = await container.plan_day.execute()

    # Transform to response model
    planned_tasks_response = [
        PlannedTaskResponse(
            task_id=_get_task_id(planned_task),
            course_name=_get_course_name(planned_task),
            title=_get_title(planned_task),
            priority=_get_priority(planned_task).value,
            estimated_minutes=planned_task.estimated_minutes,
            formatted_time_block=planned_task.formatted_time_block,
            difficulty=planned_task.difficulty.value,
            cognitive_load=planned_task.cognitive_load.value,
            sequence_position=i + 1,  # 1-indexed for UI
        )
        for i, planned_task in enumerate(day_plan.planned_tasks)
    ]

    return DayPlanResponse(
        created_at=day_plan.created_at.isoformat(),
        planned_for_date=day_plan.planned_for_date.isoformat(),
        planned_tasks=planned_tasks_response,
        total_minutes=day_plan.total_minutes,
        total_hours=round(day_plan.total_hours, 1),
        is_feasible=day_plan.is_feasible,
        cognitive_balance=day_plan.cognitive_balance,
        pending_tasks_count=day_plan.pending_tasks_count,
    )
