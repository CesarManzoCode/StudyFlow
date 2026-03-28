from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.domain.enums import TaskPriority, TaskStatus


class Task(BaseModel):
    """
    Canonical assignment entity used across the application.

    This model represents a Moodle assignment after it has already been
    scraped and normalized into the application's domain language.
    """

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
    )

    id: str = Field(..., min_length=1)
    course_name: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)

    description_html: str | None = None
    description_text: str | None = None

    due_at: datetime | None = None
    status: TaskStatus = TaskStatus.UNKNOWN

    url: str = Field(..., min_length=1)

    @computed_field
    @property
    def is_pending(self) -> bool:
        """
        Whether the task should be treated as pending work.
        """
        return self.status in {TaskStatus.PENDING, TaskStatus.OVERDUE}

    @computed_field
    @property
    def is_overdue(self) -> bool:
        """
        Whether the task is overdue according to its normalized domain status.
        """
        return self.status == TaskStatus.OVERDUE

    def with_status(self, status: TaskStatus) -> Self:
        """
        Return a new task instance with an updated status.

        The model is intentionally immutable, so state changes produce a new
        instance instead of mutating the existing one.
        """
        return self.model_copy(update={"status": status})

    def with_due_at(self, due_at: datetime | None) -> Self:
        """
        Return a new task instance with an updated due date.
        """
        return self.model_copy(update={"due_at": due_at})

    def with_priority(self, priority: TaskPriority) -> "PrioritizedTask":
        """
        Wrap this task into a prioritized domain object.
        """
        return PrioritizedTask(task=self, priority=priority)


class PrioritizedTask(BaseModel):
    """
    Read model that pairs a task with its derived priority.

    Priority is not intrinsic persistent state of the task itself; it is a
    computed classification derived from business rules.
    """

    model_config = ConfigDict(frozen=True)

    task: Task
    priority: TaskPriority