from datetime import datetime
from typing import Protocol

from app.domain.models.task import Task


class TaskRepository(Protocol):
    """
    Contract for storing and retrieving the current in-memory task state.

    This repository is intentionally scoped to the current process lifetime.
    It does not represent persistent history; it only holds the latest
    synchronized task snapshot.
    """

    async def replace_all(self, tasks: list[Task], synced_at: datetime) -> None:
        """
        Replace the entire current task snapshot with a newly synchronized one.
        """

    async def list_all(self) -> list[Task]:
        """
        Return all tasks currently stored in memory.
        """

    async def list_pending(self) -> list[Task]:
        """
        Return only tasks that are currently considered pending.
        """

    async def get_by_id(self, task_id: str) -> Task | None:
        """
        Return a task by its identifier, or None if it does not exist.
        """

    async def last_synced_at(self) -> datetime | None:
        """
        Return the timestamp of the latest successful synchronization, if any.
        """

    async def clear(self) -> None:
        """
        Remove all currently stored tasks and reset synchronization metadata.
        """