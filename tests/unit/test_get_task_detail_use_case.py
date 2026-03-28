from unittest.mock import AsyncMock

import pytest

from app.application.use_cases.get_task_detail import GetTaskDetailUseCase
from app.domain.enums import TaskStatus
from app.domain.exceptions import TaskNotFoundError
from app.domain.models.task import Task


@pytest.mark.asyncio
async def test_execute_returns_task_when_found() -> None:
    task = Task(
        id="task-1",
        course_name="Physics",
        title="Lab report",
        status=TaskStatus.PENDING,
        url="https://example.edu/task-1",
    )
    repository = AsyncMock()
    repository.get_by_id = AsyncMock(return_value=task)

    use_case = GetTaskDetailUseCase(task_repository=repository)

    result = await use_case.execute("task-1")

    assert result == task


@pytest.mark.asyncio
async def test_execute_raises_not_found_when_missing() -> None:
    repository = AsyncMock()
    repository.get_by_id = AsyncMock(return_value=None)

    use_case = GetTaskDetailUseCase(task_repository=repository)

    with pytest.raises(TaskNotFoundError):
        await use_case.execute("missing")
