from datetime import datetime, timedelta

from app.domain.enums import TaskPriority
from app.domain.models.task import PrioritizedTask, Task


class TaskPriorityService:
    """
    Derive priority levels for tasks based exclusively on time remaining until
    their deadline.

    Priority rules are intentionally simple and deterministic:

    - overdue tasks -> critical
    - due within 24 hours -> critical
    - due within 72 hours -> high
    - due within 7 days -> medium
    - due later than 7 days -> low
    - no due date -> none
    """

    def prioritize(self, task: Task, now: datetime) -> PrioritizedTask:
        """
        Compute the priority for a single task and return a prioritized view.
        """
        priority = self._resolve_priority(task=task, now=now)
        return task.with_priority(priority)

    def prioritize_many(self, tasks: list[Task], now: datetime) -> list[PrioritizedTask]:
        """
        Compute priorities for multiple tasks and return them sorted from most
        urgent to least urgent.

        Sorting rules:
        1. higher priority first
        2. earlier due date first
        3. course name ascending
        4. title ascending
        """
        prioritized_tasks = [self.prioritize(task=task, now=now) for task in tasks]

        return sorted(
            prioritized_tasks,
            key=self._sort_key,
        )

    def _resolve_priority(self, task: Task, now: datetime) -> TaskPriority:
        if task.due_at is None:
            return TaskPriority.NONE

        time_remaining = task.due_at - now

        if time_remaining <= timedelta(hours=24):
            return TaskPriority.CRITICAL

        if time_remaining <= timedelta(hours=72):
            return TaskPriority.HIGH

        if time_remaining <= timedelta(days=7):
            return TaskPriority.MEDIUM

        return TaskPriority.LOW

    def _sort_key(self, prioritized_task: PrioritizedTask) -> tuple[int, datetime, str, str]:
        task = prioritized_task.task

        priority_rank = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3,
            TaskPriority.NONE: 4,
        }

        due_at = task.due_at or datetime.max

        return (
            priority_rank[prioritized_task.priority],
            due_at,
            task.course_name.casefold(),
            task.title.casefold(),
        )