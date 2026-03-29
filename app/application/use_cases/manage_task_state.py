from datetime import datetime

from app.domain.models.task_state import AIInteraction, ChecklistItem, TaskState
from app.domain.ports.state_repository import StateRepository


class GetTaskStateUseCase:
    """
    Retrieve persistent state for a single task.

    If no state exists for the task, returns None.
    Clients can then decide to create new state or handle the absence.
    """

    def __init__(self, state_repo: StateRepository) -> None:
        self._state_repo = state_repo

    async def execute(self, task_id: str) -> TaskState | None:
        """
        Get task state by ID.
        """
        return await self._state_repo.get_by_task_id(task_id)


class UpdateTaskNotesUseCase:
    """
    Update or create quick notes for a task.
    """

    def __init__(self, state_repo: StateRepository) -> None:
        self._state_repo = state_repo

    async def execute(self, task_id: str, notes: str) -> TaskState:
        """
        Update task notes. Creates a new TaskState if it doesn't exist.
        """
        existing_state = await self._state_repo.get_by_task_id(task_id)

        if existing_state:
            new_state = existing_state.with_notes(notes)
        else:
            new_state = TaskState(
                task_id=task_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                notes=notes.strip(),
            )

        await self._state_repo.save(new_state)
        return new_state


class UpdateTaskChecklistUseCase:
    """
    Replace or update the entire checklist for a task.
    """

    def __init__(self, state_repo: StateRepository) -> None:
        self._state_repo = state_repo

    async def execute(
        self, task_id: str, checklist_items: list[dict]
    ) -> TaskState:
        """
        Update checklist. Creates a new TaskState if it doesn't exist.

        Args:
            task_id: Moodle task ID
            checklist_items: List of dicts with 'text' and optional 'completed' keys
        """
        new_checklist = []
        for item in checklist_items:
            new_checklist.append(
                ChecklistItem(
                    text=item.get("text", ""),
                    completed=item.get("completed", False),
                    completed_at=(
                        datetime.utcnow()
                        if item.get("completed")
                        else None
                    ),
                )
            )

        existing_state = await self._state_repo.get_by_task_id(task_id)

        if existing_state:
            new_state = existing_state.with_checklist(new_checklist)
        else:
            new_state = TaskState(
                task_id=task_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                checklist=new_checklist,
            )

        await self._state_repo.save(new_state)
        return new_state


class ToggleChecklistItemUseCase:
    """
    Toggle the completion status of a single checklist item by index.
    """

    def __init__(self, state_repo: StateRepository) -> None:
        self._state_repo = state_repo

    async def execute(self, task_id: str, item_index: int) -> TaskState:
        """
        Toggle a checklist item. Raises ValueError if task state doesn't exist
        or index is out of range.
        """
        existing_state = await self._state_repo.get_by_task_id(task_id)

        if not existing_state:
            raise ValueError(
                f"No task state exists for task {task_id}. Create state first."
            )

        new_state = existing_state.toggle_checklist_item(item_index)
        await self._state_repo.save(new_state)
        return new_state


class RecordAIInteractionUseCase:
    """
    Record a user interaction with the AI help system.
    """

    def __init__(self, state_repo: StateRepository) -> None:
        self._state_repo = state_repo

    async def execute(
        self,
        task_id: str,
        interaction_id: str,
        question: str,
        response: str | None = None,
        metadata: dict | None = None,
    ) -> TaskState:
        """
        Record an AI interaction for a task.
        Creates a new TaskState if it doesn't exist.
        """
        interaction = AIInteraction(
            interaction_id=interaction_id,
            timestamp=datetime.utcnow(),
            question=question.strip(),
            response=response.strip() if response else None,
            metadata=metadata or {},
        )

        existing_state = await self._state_repo.get_by_task_id(task_id)

        if existing_state:
            new_state = existing_state.with_ai_interaction(interaction)
        else:
            new_state = TaskState(
                task_id=task_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                ai_interactions=[interaction],
            )

        await self._state_repo.save(new_state)
        return new_state
