from datetime import datetime

from app.domain.enums import TaskPriority, TaskStatus
from app.domain.models.task import Task


def _task() -> Task:
    return Task(
        id="task-1",
        course_name="Logic",
        title="Essay",
        due_at=datetime(2026, 4, 3, 12, 0),
        status=TaskStatus.PENDING,
        url="https://example.edu/task-1",
    )


def test_task_with_status_returns_new_instance() -> None:
    task = _task()

    updated = task.with_status(TaskStatus.SUBMITTED)

    assert updated.status == TaskStatus.SUBMITTED
    assert task.status == TaskStatus.PENDING


def test_task_with_due_at_returns_new_instance() -> None:
    task = _task()
    new_due_at = datetime(2026, 4, 10, 10, 0)

    updated = task.with_due_at(new_due_at)

    assert updated.due_at == new_due_at
    assert task.due_at != new_due_at


def test_task_with_priority_wraps_in_prioritized_task() -> None:
    task = _task()

    prioritized = task.with_priority(TaskPriority.HIGH)

    assert prioritized.task == task
    assert prioritized.priority == TaskPriority.HIGH
