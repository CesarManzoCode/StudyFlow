from datetime import datetime, timedelta

import pytest

from app.domain.enums import TaskStatus
from app.domain.models.task import Task
from app.infrastructure.cache.in_memory_task_store import InMemoryTaskStore


def _task(task_id: str, *, status: TaskStatus = TaskStatus.PENDING) -> Task:
    return Task(
        id=task_id,
        course_name="Systems",
        title=f"Task {task_id}",
        due_at=datetime(2026, 4, 2, 10, 0),
        status=status,
        url=f"https://example.edu/{task_id}",
    )


@pytest.mark.asyncio
async def test_store_replace_list_and_get_by_id() -> None:
    store = InMemoryTaskStore()
    synced_at = datetime(2026, 3, 28, 12, 0, 0)
    tasks = [_task("a"), _task("b", status=TaskStatus.SUBMITTED)]

    await store.replace_all(tasks=tasks, synced_at=synced_at)

    listed = await store.list_all()
    assert {task.id for task in listed} == {"a", "b"}

    loaded = await store.get_by_id("a")
    assert loaded is not None
    assert loaded.id == "a"

    assert await store.last_synced_at() == synced_at


@pytest.mark.asyncio
async def test_store_list_pending_filters_non_pending_tasks() -> None:
    store = InMemoryTaskStore()
    await store.replace_all(
        tasks=[
            _task("pending", status=TaskStatus.PENDING),
            _task("overdue", status=TaskStatus.OVERDUE),
            _task("submitted", status=TaskStatus.SUBMITTED),
            _task("unknown", status=TaskStatus.UNKNOWN),
        ],
        synced_at=datetime.now() - timedelta(minutes=3),
    )

    pending = await store.list_pending()
    assert {task.id for task in pending} == {"pending", "overdue"}


@pytest.mark.asyncio
async def test_store_clear_resets_data_and_sync_time() -> None:
    store = InMemoryTaskStore()
    await store.replace_all(tasks=[_task("a")], synced_at=datetime.now())

    await store.clear()

    assert await store.list_all() == []
    assert await store.last_synced_at() is None
