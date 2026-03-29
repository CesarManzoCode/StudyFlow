"""
API routes for AI task assistance with enhanced step details.
"""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.domain.models.task_step import TaskStep, StepDifficulty
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


def _convert_string_steps_to_task_steps(step_strings: list[str]) -> list[TaskStep]:
    """
    Convert simple string steps into enriched TaskStep objects.
    
    Applies heuristics to estimate time and difficulty from step descriptions.
    The first step is marked as the minimal first step.
    """
    task_steps = []
    
    for i, step_str in enumerate(step_strings):
        # Estimate time based on keywords and position
        minutes = _estimate_minutes_from_description(step_str)
        difficulty = _infer_difficulty_from_description(step_str)
        is_first = (i == 0)  # First step is the minimal one
        
        task_step = TaskStep(
            description=step_str,
            estimated_minutes=minutes,
            difficulty=difficulty,
            is_minimal_first_step=is_first,
        )
        task_steps.append(task_step)
    
    return task_steps


def _estimate_minutes_from_description(description: str) -> int:
    """
    Heuristic time estimation based on step description keywords.
    """
    description_lower = description.lower()
    
    # Trivial: < 1 minute
    trivial_keywords = ["open", "click", "close", "view", "see", "read"]
    for kw in trivial_keywords:
        if kw in description_lower:
            return 1
    
    # Easy: 1-5 minutes
    easy_keywords = ["review", "check", "copy", "paste", "download"]
    for kw in easy_keywords:
        if kw in description_lower:
            return 3
    
    # Moderate: 5-15 minutes
    moderate_keywords = ["write", "edit", "create", "prepare", "organize", "analyze"]
    for kw in moderate_keywords:
        if kw in description_lower:
            return 10
    
    # Hard: 15+ minutes
    hard_keywords = ["develop", "implement", "design", "complete", "solve", "research"]
    for kw in hard_keywords:
        if kw in description_lower:
            return 20
    
    # Default: 5 minutes
    return 5


def _infer_difficulty_from_description(description: str) -> StepDifficulty:
    """
    Infer difficulty from step description keywords.
    """
    description_lower = description.lower()
    
    # Trivial
    trivial_keywords = ["open", "click", "close", "view", "read", "check"]
    for kw in trivial_keywords:
        if kw in description_lower:
            return StepDifficulty.TRIVIAL
    
    # Easy
    easy_keywords = ["review", "copy", "paste", "simple", "basic", "download"]
    for kw in easy_keywords:
        if kw in description_lower:
            return StepDifficulty.EASY
    
    # Hard
    hard_keywords = ["complex", "difficult", "advanced", "challenging", "develop", "implement"]
    for kw in hard_keywords:
        if kw in description_lower:
            return StepDifficulty.HARD
    
    # Default: moderate
    return StepDifficulty.MODERATE


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
    
    # Generate the checklist
    checklist = await container.generate_task_help.execute(
        task_id=task_id,
        user_question=user_question,
    )
    
    # Convert string steps to enriched TaskSteps
    enhanced_steps = _convert_string_steps_to_task_steps(checklist.steps)
    
    # Find minimal first step
    minimal_step_response = None
    if enhanced_steps:
        minimal_step = enhanced_steps[0]  # First enhanced step is always minimal
        minimal_step_response = TaskStepResponse(
            description=minimal_step.description,
            estimated_minutes=minimal_step.estimated_minutes,
            difficulty=minimal_step.difficulty.value,
            is_minimal_first_step=True,
            effort_indicator=minimal_step.effort_indicator,
            formatted_time=minimal_step.formatted_time,
        )
    
    # Convert all enhanced steps to response format
    steps_response = [
        TaskStepResponse(
            description=step.description,
            estimated_minutes=step.estimated_minutes,
            difficulty=step.difficulty.value,
            is_minimal_first_step=step.is_minimal_first_step,
            effort_indicator=step.effort_indicator,
            formatted_time=step.formatted_time,
        )
        for step in enhanced_steps
    ]
    
    total_minutes = sum(step.estimated_minutes for step in enhanced_steps)
    
    return EnhancedChecklistResponseApi(
        summary=checklist.summary,
        deliverable=checklist.deliverable,
        steps=steps_response,
        warnings=checklist.warnings,
        questions_to_clarify=checklist.questions_to_clarify,
        final_checklist=checklist.final_checklist,
        total_estimated_minutes=total_minutes,
        minimal_first_step=minimal_step_response,
        has_minimal_first_step=bool(minimal_step_response),
    )
