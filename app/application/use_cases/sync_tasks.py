from datetime import datetime

from app.domain.models.task import Task
from app.domain.ports.moodle_client import MoodleClient
from app.domain.ports.task_repository import TaskRepository


class SyncTasksUseCase:
    """
    Synchronize the current Moodle task snapshot into the in-memory repository.
    """

    def __init__(
        self,
        moodle_client: MoodleClient,
        task_repository: TaskRepository,
    ) -> None:
        self._moodle_client = moodle_client
        self._task_repository = task_repository

    async def execute(self, synced_at: datetime) -> list[Task]:
        """
        Fetch the latest Moodle task snapshot and replace the in-memory state.

        Args:
            synced_at: Timestamp representing when the synchronization is
                considered to have happened.

        Returns:
            The normalized synchronized task list.

        Raises:
            MoodleAuthenticationError:
                If Moodle authentication fails.
            MoodleScrapingError:
                If Moodle data cannot be fetched or normalized.
        """
        tasks = await self._moodle_client.fetch_tasks()
        await self._task_repository.replace_all(tasks=tasks, synced_at=synced_at)
        return tasks