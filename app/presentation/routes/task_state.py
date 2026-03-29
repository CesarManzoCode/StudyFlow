"""
API routes for managing persistent task state.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.domain.models.task_state import TaskState
from app.infrastructure.factories import AppContainer, build_app_container


router = APIRouter(prefix="/api/task-state", tags=["task-state"])


def _get_container() -> AppContainer:
    """Dependency injection for AppContainer."""
    return build_app_container()


# =========================================================
# REQUEST/RESPONSE MODELS
# =========================================================


class ChecklistItemRequest(BaseModel):
    """Request model for checklist item."""

    text: str = Field(..., min_length=1)
    completed: bool = Field(default=False)


class UpdateNotesRequest(BaseModel):
    """Request model for updating task notes."""

    notes: str = Field(default="")


class UpdateChecklistRequest(BaseModel):
    """Request model for updating checklist."""

    checklist: list[ChecklistItemRequest] = Field(default_factory=list)


class ToggleItemRequest(BaseModel):
    """Request model for toggling checklist item."""

    item_index: int = Field(..., ge=0)


class RecordInteractionRequest(BaseModel):
    """Request model for recording AI interaction."""

    interaction_id: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1)
    response: str | None = None
    metadata: dict | None = None


class TaskStateResponse(BaseModel):
    """Response model for task state."""

    task_id: str
    completion_rate: float


# =========================================================
# ENDPOINTS
# =========================================================


@router.get("/{task_id}", response_model=TaskState | None)
async def get_task_state(
    task_id: str,
    container: AppContainer = Depends(_get_container),
) -> TaskState | None:
    """
    Retrieve persistent state for a task.

    Returns the full task state including checklist, notes, and AI interactions.
    Returns None if no state exists for the task.
    """
    return await container.get_task_state.execute(task_id=task_id)


@router.patch("/{task_id}/notes", response_model=TaskStateResponse)
async def update_task_notes(
    task_id: str,
    request: UpdateNotesRequest,
    container: AppContainer = Depends(_get_container),
) -> TaskStateResponse:
    """
    Update or create notes for a task.

    If task state doesn't exist, it will be created.
    """
    state = await container.update_task_notes.execute(
        task_id=task_id,
        notes=request.notes,
    )
    return TaskStateResponse(
        task_id=state.task_id,
        completion_rate=state.completion_rate,
    )


@router.patch("/{task_id}/checklist", response_model=TaskStateResponse)
async def update_task_checklist(
    task_id: str,
    request: UpdateChecklistRequest,
    container: AppContainer = Depends(_get_container),
) -> TaskStateResponse:
    """
    Replace or update the checklist for a task.

    If task state doesn't exist, it will be created.
    """
    checklist_data = [item.model_dump() for item in request.checklist]
    state = await container.update_task_checklist.execute(
        task_id=task_id,
        checklist_items=checklist_data,
    )
    return TaskStateResponse(
        task_id=state.task_id,
        completion_rate=state.completion_rate,
    )


@router.patch("/{task_id}/checklist/{item_index}/toggle", response_model=TaskStateResponse)
async def toggle_checklist_item(
    task_id: str,
    item_index: int,
    container: AppContainer = Depends(_get_container),
) -> TaskStateResponse:
    """
    Toggle the completion status of a single checklist item.

    Requires existing task state (raises 404 if not found).
    """
    try:
        state = await container.toggle_checklist_item.execute(
            task_id=task_id,
            item_index=item_index,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return TaskStateResponse(
        task_id=state.task_id,
        completion_rate=state.completion_rate,
    )


@router.post("/{task_id}/interactions", response_model=TaskStateResponse)
async def record_ai_interaction(
    task_id: str,
    request: RecordInteractionRequest,
    container: AppContainer = Depends(_get_container),
) -> TaskStateResponse:
    """
    Record a user interaction with the AI help system.

    Creates or updates task state depending on existence.
    """
    state = await container.record_ai_interaction.execute(
        task_id=task_id,
        interaction_id=request.interaction_id,
        question=request.question,
        response=request.response,
        metadata=request.metadata,
    )
    return TaskStateResponse(
        task_id=state.task_id,
        completion_rate=state.completion_rate,
    )
