from app.domain.exceptions import TaskNotFoundError
from app.domain.models.task import Task
from app.domain.ports.task_repository import TaskRepository


class GetTaskDetailUseCase:
    """
    Retrieve a single task from the current in-memory snapshot.
    """

    def __init__(self, task_repository: TaskRepository) -> None:
        self._task_repository = task_repository

    async def execute(self, task_id: str) -> Task:
        """
        Return the task identified by the given task ID.

        Args:
            task_id: The normalized task identifier.

        Returns:
            The matching task from the current in-memory snapshot.

        Raises:
            TaskNotFoundError:
                If the task does not exist in the current snapshot.
        """
        task = await self._task_repository.get_by_id(task_id)
        if task is None:
            msg = f"Task with id '{task_id}' was not found."
            raise TaskNotFoundError(msg)

        return task