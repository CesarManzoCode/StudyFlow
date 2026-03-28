from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from app.application.use_cases.list_tasks import ListTasksUseCase


@pytest.mark.asyncio
async def test_execute_loads_pending_tasks_and_prioritizes_them() -> None:
    now = datetime(2026, 3, 28, 12, 0, 0)
    pending_tasks = [Mock(name="task-1"), Mock(name="task-2")]
    prioritized = [Mock(name="prioritized-1")]

    repository = AsyncMock()
    repository.list_pending = AsyncMock(return_value=pending_tasks)

    priority_service = Mock()
    priority_service.prioritize_many = Mock(return_value=prioritized)

    use_case = ListTasksUseCase(
        task_repository=repository,
        task_priority_service=priority_service,
    )

    result = await use_case.execute(now=now)

    assert result == prioritized
    repository.list_pending.assert_awaited_once_with()
    priority_service.prioritize_many.assert_called_once_with(tasks=pending_tasks, now=now)
