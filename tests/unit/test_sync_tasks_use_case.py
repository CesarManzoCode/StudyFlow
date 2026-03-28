from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.application.use_cases.sync_tasks import SyncTasksUseCase
from app.domain.enums import TaskStatus
from app.domain.models.task import Task


@pytest.mark.asyncio
async def test_execute_fetches_and_replaces_repository_snapshot() -> None:
    synced_at = datetime(2026, 3, 28, 12, 0, 0)
    tasks = [
        Task(
            id="task-1",
            course_name="Compilers",
            title="Homework",
            status=TaskStatus.PENDING,
            url="https://example.edu/task-1",
        )
    ]

    moodle_client = AsyncMock()
    moodle_client.fetch_tasks = AsyncMock(return_value=tasks)

    repository = AsyncMock()
    repository.replace_all = AsyncMock(return_value=None)

    use_case = SyncTasksUseCase(moodle_client=moodle_client, task_repository=repository)

    result = await use_case.execute(synced_at=synced_at)

    assert result == tasks
    moodle_client.fetch_tasks.assert_awaited_once_with()
    repository.replace_all.assert_awaited_once_with(tasks=tasks, synced_at=synced_at)
