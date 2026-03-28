from asyncio import Lock
from datetime import datetime

from app.domain.models.task import Task
from app.domain.ports.task_repository import TaskRepository


class InMemoryTaskStore(TaskRepository):
    """
    In-memory task repository for the current application process.

    This store keeps only the latest synchronized snapshot and its associated
    synchronization timestamp. It is intentionally non-persistent.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self._tasks_by_id: dict[str, Task] = {}
        self._last_synced_at: datetime | None = None

    async def replace_all(self, tasks: list[Task], synced_at: datetime) -> None:
        """
        Replace the current snapshot atomically.
        """
        new_tasks_by_id = {task.id: task for task in tasks}

        async with self._lock:
            self._tasks_by_id = new_tasks_by_id
            self._last_synced_at = synced_at

    async def list_all(self) -> list[Task]:
        """
        Return all tasks currently stored in memory.
        """
        async with self._lock:
            return list(self._tasks_by_id.values())

    async def list_pending(self) -> list[Task]:
        """
        Return all tasks currently considered pending.
        """
        async with self._lock:
            return [task for task in self._tasks_by_id.values() if task.is_pending]

    async def get_by_id(self, task_id: str) -> Task | None:
        """
        Return a task by ID if present.
        """
        async with self._lock:
            return self._tasks_by_id.get(task_id)

    async def last_synced_at(self) -> datetime | None:
        """
        Return the latest successful synchronization timestamp, if any.
        """
        async with self._lock:
            return self._last_synced_at

    async def clear(self) -> None:
        """
        Clear the current snapshot and synchronization metadata.
        """
        async with self._lock:
            self._tasks_by_id = {}
            self._last_synced_at = None