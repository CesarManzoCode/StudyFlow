from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.models.task import Task
from app.domain.enums import TaskPriority


@dataclass(frozen=True, slots=True)
class TaskViewModel:
    """
    UI-ready representation of a task.
    """

    id: str
    title: str
    course_name: str
    status: str
    due_at: str | None


@dataclass(frozen=True, slots=True)
class TaskListItemViewModel:
    """
    Combines task data with priority for dashboard rendering.
    """

    task: TaskViewModel
    priority: TaskPriority


# =========================================================
# MAPPERS
# =========================================================

def map_task_to_viewmodel(task: Task) -> TaskViewModel:
    """
    Convert domain Task into UI-safe structure.
    """
    return TaskViewModel(
        id=task.id,
        title=task.title,
        course_name=task.course_name,
        status=task.status.value,
        due_at=_format_datetime(task.due_at),
    )


def map_task_list(
    tasks_with_priority: list[tuple[Task, TaskPriority]],
) -> list[TaskListItemViewModel]:
    """
    Convert domain list into UI-ready list.
    """
    result: list[TaskListItemViewModel] = []

    for task, priority in tasks_with_priority:
        result.append(
            TaskListItemViewModel(
                task=map_task_to_viewmodel(task),
                priority=priority,
            )
        )

    return result


# =========================================================
# HELPERS
# =========================================================

def _format_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None

    return value.strftime("%Y-%m-%d %H:%M")