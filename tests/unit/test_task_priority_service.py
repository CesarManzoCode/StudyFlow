from datetime import datetime, timedelta

from app.application.services.task_priority_service import TaskPriorityService
from app.domain.enums import TaskPriority, TaskStatus
from app.domain.models.task import Task


def _task(*, task_id: str, due_at: datetime | None, course: str = "Course", title: str = "Task") -> Task:
    return Task(
        id=task_id,
        course_name=course,
        title=title,
        due_at=due_at,
        status=TaskStatus.PENDING,
        url=f"https://example.edu/{task_id}",
    )


def test_prioritize_boundaries() -> None:
    service = TaskPriorityService()
    now = datetime(2026, 3, 28, 10, 0, 0)

    cases = [
        (_task(task_id="none", due_at=None), TaskPriority.NONE),
        (_task(task_id="overdue", due_at=now - timedelta(minutes=1)), TaskPriority.CRITICAL),
        (_task(task_id="24h", due_at=now + timedelta(hours=24)), TaskPriority.CRITICAL),
        (_task(task_id="25h", due_at=now + timedelta(hours=25)), TaskPriority.HIGH),
        (_task(task_id="72h", due_at=now + timedelta(hours=72)), TaskPriority.HIGH),
        (_task(task_id="73h", due_at=now + timedelta(hours=73)), TaskPriority.MEDIUM),
        (_task(task_id="7d", due_at=now + timedelta(days=7)), TaskPriority.MEDIUM),
        (_task(task_id="8d", due_at=now + timedelta(days=8)), TaskPriority.LOW),
    ]

    for task, expected in cases:
        prioritized = service.prioritize(task=task, now=now)
        assert prioritized.priority == expected


def test_prioritize_many_sorts_by_priority_due_course_and_title() -> None:
    service = TaskPriorityService()
    now = datetime(2026, 3, 28, 10, 0, 0)

    tasks = [
        _task(task_id="none-1", due_at=None, course="Zeta", title="B"),
        _task(task_id="critical-1", due_at=now + timedelta(hours=1), course="Math", title="B"),
        _task(task_id="critical-2", due_at=now + timedelta(hours=2), course="Math", title="A"),
        _task(task_id="high-1", due_at=now + timedelta(hours=30), course="History", title="A"),
        _task(task_id="medium-a", due_at=now + timedelta(days=4), course="Biology", title="Z"),
        _task(task_id="medium-b", due_at=now + timedelta(days=4), course="Biology", title="A"),
    ]

    prioritized = service.prioritize_many(tasks=tasks, now=now)
    ordered_ids = [item.task.id for item in prioritized]

    assert ordered_ids == [
        "critical-1",
        "critical-2",
        "high-1",
        "medium-b",
        "medium-a",
        "none-1",
    ]
