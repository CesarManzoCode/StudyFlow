"""API routes for AI task assistance with enhanced step details."""

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.infrastructure.factories import AppContainer


router = APIRouter(prefix="/api/tasks", tags=["ai-help"])


def _get_container(request: Request) -> AppContainer:
    """Get the shared application container from app state."""
    return request.app.state.container


class TaskStepResponse(BaseModel):
    """Response model for a task step."""
    description: str
    estimated_minutes: int
    difficulty: str
    is_minimal_first_step: bool
    effort_indicator: str
    formatted_time: str


class EnhancedChecklistResponseApi(BaseModel):
    """API response with enhanced step information."""
    summary: str
    deliverable: str
    steps: list[TaskStepResponse]
    warnings: list[str]
    questions_to_clarify: list[str]
    final_checklist: list[str]
    total_estimated_minutes: int
    minimal_first_step: TaskStepResponse | None
    has_minimal_first_step: bool


@router.post("/{task_id}/help/enhanced")
async def generate_enhanced_task_help(
    request: Request,
    task_id: str,
    user_question: str | None = None,
) -> EnhancedChecklistResponseApi:
    """
    Generate AI help for a task with enhanced step details.
    
    Each step includes:
    - Estimated time in minutes
    - Difficulty level (trivial, easy, moderate, hard)
    - Whether it's the "minimal first step" to overcome procrastination
    
    Returns:
        Enhanced checklist with time and difficulty estimates
    """
    container = _get_container(request)
    
    checklist = await container.generate_task_help.execute_enhanced(
        task_id=task_id,
        user_question=user_question,
    )

    steps_response = [
        TaskStepResponse(
            description=step.description,
            estimated_minutes=step.estimated_minutes,
            difficulty=step.difficulty.value,
            is_minimal_first_step=step.is_minimal_first_step,
            effort_indicator=step.effort_indicator,
            formatted_time=step.formatted_time,
        )
        for step in checklist.steps
    ]

    minimal_step_response = None
    if checklist.minimal_first_step is not None:
        step = checklist.minimal_first_step
        minimal_step_response = TaskStepResponse(
            description=step.description,
            estimated_minutes=step.estimated_minutes,
            difficulty=step.difficulty.value,
            is_minimal_first_step=step.is_minimal_first_step,
            effort_indicator=step.effort_indicator,
            formatted_time=step.formatted_time,
        )
    
    return EnhancedChecklistResponseApi(
        summary=checklist.summary,
        deliverable=checklist.deliverable,
        steps=steps_response,
        warnings=checklist.warnings,
        questions_to_clarify=checklist.questions_to_clarify,
        final_checklist=checklist.final_checklist,
        total_estimated_minutes=checklist.total_estimated_minutes,
        minimal_first_step=minimal_step_response,
        has_minimal_first_step=checklist.has_minimal_first_step,
    )
