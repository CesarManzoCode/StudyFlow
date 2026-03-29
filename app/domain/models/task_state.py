from datetime import datetime
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field


class ChecklistItem(BaseModel):
    """
    Individual item in a task's persistent checklist.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    text: str = Field(..., min_length=1)
    completed: bool = Field(default=False)
    completed_at: datetime | None = None


class AIInteraction(BaseModel):
    """
    Record of a user interaction with the AI help system for this task.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    interaction_id: str = Field(..., min_length=1)
    timestamp: datetime
    question: str = Field(..., min_length=1)
    response: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskState(BaseModel):
    """
    Persistent state for a Moodle task.

    This model represents user-created state that persists across application
    restarts, unlike the Task model which is ephemeral (synced from Moodle).

    The state is indexed by task ID and includes:
    - Custom checklist items (created by user or AI)
    - Progress tracking (check/uncheck items)
    - Quick notes
    - Interaction history with AI
    """

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
    )

    task_id: str = Field(..., min_length=1, description="Moodle task identifier")
    created_at: datetime
    updated_at: datetime

    checklist: list[ChecklistItem] = Field(
        default_factory=list,
        description="Custom checklist items for this task",
    )

    notes: str = Field(
        default="",
        description="Quick user notes for this task",
    )

    ai_interactions: list[AIInteraction] = Field(
        default_factory=list,
        description="History of interactions with AI for this task",
    )

    @property
    def completion_rate(self) -> float:
        """
        Calculate progress as percentage of completed items.
        """
        if not self.checklist:
            return 0.0

        completed = sum(1 for item in self.checklist if item.completed)
        return (completed / len(self.checklist)) * 100.0

    def with_notes(self, notes: str) -> Self:
        """
        Return a new TaskState with updated notes.
        """
        return self.model_copy(
            update={"notes": notes.strip(), "updated_at": datetime.utcnow()}
        )

    def with_checklist(self, checklist: list[ChecklistItem]) -> Self:
        """
        Return a new TaskState with updated checklist.
        """
        return self.model_copy(
            update={"checklist": checklist, "updated_at": datetime.utcnow()}
        )

    def with_ai_interaction(self, interaction: AIInteraction) -> Self:
        """
        Return a new TaskState with an added AI interaction record.
        """
        new_interactions = self.ai_interactions + [interaction]
        return self.model_copy(
            update={
                "ai_interactions": new_interactions,
                "updated_at": datetime.utcnow(),
            }
        )

    def toggle_checklist_item(self, index: int) -> Self:
        """
        Toggle the completion status of a checklist item by index.
        """
        if not (0 <= index < len(self.checklist)):
            raise ValueError(f"Checklist index {index} out of range")

        new_checklist = list(self.checklist)
        item = new_checklist[index]

        new_checklist[index] = item.model_copy(
            update={
                "completed": not item.completed,
                "completed_at": datetime.utcnow() if not item.completed else None,
            }
        )

        return self.with_checklist(new_checklist)
