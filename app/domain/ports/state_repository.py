from typing import Protocol

from app.domain.models.task_state import TaskState


class StateRepository(Protocol):
    """
    Contract for storing and retrieving persistent task state.

    This repository handles all user-created persistent data:
    - Custom checklists
    - Progress tracking
    - Quick notes
    - AI interaction history

    State is indexed by Moodle task ID and survives across application restarts.
    """

    async def save(self, state: TaskState) -> None:
        """
        Persist a task state (create or update).
        """

    async def get_by_task_id(self, task_id: str) -> TaskState | None:
        """
        Retrieve a task state by its Moodle task ID.
        Returns None if no state exists for the task.
        """

    async def get_all(self) -> dict[str, TaskState]:
        """
        Retrieve all stored task states.
        Returns a dict keyed by task_id.
        """

    async def delete(self, task_id: str) -> bool:
        """
        Delete a task state by its ID.
        Returns True if deleted, False if not found.
        """

    async def clear_all(self) -> None:
        """
        Delete all stored task states.
        """
