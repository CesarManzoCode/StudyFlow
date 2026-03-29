"""
Unit tests for TaskState domain model.
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from app.domain.models.task_state import AIInteraction, ChecklistItem, TaskState


class TestChecklistItem:
    """Test ChecklistItem domain model."""

    def test_create_incomplete_item(self) -> None:
        """Should create uncompleted checklist item."""
        item = ChecklistItem(text="Review requirements")
        assert item.text == "Review requirements"
        assert item.completed is False
        assert item.completed_at is None

    def test_create_completed_item(self) -> None:
        """Should create completed checklist item."""
        now = datetime.utcnow()
        item = ChecklistItem(text="Submit draft", completed=True, completed_at=now)
        assert item.completed is True
        assert item.completed_at == now

    def test_whitespace_stripping(self) -> None:
        """Should strip whitespace from text."""
        item = ChecklistItem(text="  Read chapter 5  ")
        assert item.text == "Read chapter 5"


class TestAIInteraction:
    """Test AIInteraction domain model."""

    def test_create_interaction(self) -> None:
        """Should create AI interaction record."""
        now = datetime.utcnow()
        interaction = AIInteraction(
            interaction_id="ai-001",
            timestamp=now,
            question="How to structure the essay?",
            response="First create an outline...",
        )
        assert interaction.interaction_id == "ai-001"
        assert interaction.question == "How to structure the essay?"
        assert interaction.response == "First create an outline..."

    def test_interaction_with_metadata(self) -> None:
        """Should store arbitrary metadata."""
        metadata = {"model": "gpt-4", "tokens_used": 150}
        interaction = AIInteraction(
            interaction_id="ai-002",
            timestamp=datetime.utcnow(),
            question="Next step?",
            metadata=metadata,
        )
        assert interaction.metadata == metadata


class TestTaskState:
    """Test TaskState domain model."""

    def test_create_new_state(self) -> None:
        """Should create new task state."""
        now = datetime.utcnow()
        state = TaskState(
            task_id="task-123",
            created_at=now,
            updated_at=now,
        )
        assert state.task_id == "task-123"
        assert state.notes == ""
        assert state.checklist == []
        assert state.ai_interactions == []

    def test_completion_rate_empty_checklist(self) -> None:
        """Completion rate should be 0% for empty checklist."""
        state = TaskState(
            task_id="task-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert state.completion_rate == 0.0

    def test_completion_rate_partial(self) -> None:
        """Completion rate should be percentage of completed items."""
        state = TaskState(
            task_id="task-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            checklist=[
                ChecklistItem(text="Item 1", completed=True),
                ChecklistItem(text="Item 2", completed=False),
                ChecklistItem(text="Item 3", completed=True),
            ],
        )
        assert state.completion_rate == pytest.approx(66.66, rel=0.01)

    def test_completion_rate_full(self) -> None:
        """Completion rate should be 100% when all items completed."""
        state = TaskState(
            task_id="task-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            checklist=[
                ChecklistItem(text="Item 1", completed=True),
                ChecklistItem(text="Item 2", completed=True),
            ],
        )
        assert state.completion_rate == 100.0

    def test_with_notes_returns_new_instance(self) -> None:
        """with_notes should return new state instance."""
        state1 = TaskState(
            task_id="task-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            notes="Old note",
        )
        state2 = state1.with_notes("New note")

        assert state1.notes == "Old note"
        assert state2.notes == "New note"
        assert state2.updated_at >= state1.updated_at

    def test_with_checklist_returns_new_instance(self) -> None:
        """with_checklist should return new state instance."""
        state1 = TaskState(
            task_id="task-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        new_items = [
            ChecklistItem(text="Step 1"),
            ChecklistItem(text="Step 2"),
        ]
        state2 = state1.with_checklist(new_items)

        assert len(state1.checklist) == 0
        assert len(state2.checklist) == 2
        assert state2.checklist[0].text == "Step 1"

    def test_with_ai_interaction_returns_new_instance(self) -> None:
        """with_ai_interaction should append interaction."""
        state1 = TaskState(
            task_id="task-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        interaction = AIInteraction(
            interaction_id="ai-001",
            timestamp=datetime.utcnow(),
            question="Help?",
        )
        state2 = state1.with_ai_interaction(interaction)

        assert len(state1.ai_interactions) == 0
        assert len(state2.ai_interactions) == 1
        assert state2.ai_interactions[0].interaction_id == "ai-001"

    def test_toggle_checklist_item_incomplete_to_complete(self) -> None:
        """Should toggle item from incomplete to complete."""
        state1 = TaskState(
            task_id="task-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            checklist=[
                ChecklistItem(text="Task A", completed=False),
                ChecklistItem(text="Task B", completed=False),
            ],
        )
        state2 = state1.toggle_checklist_item(0)

        assert state1.checklist[0].completed is False
        assert state2.checklist[0].completed is True
        assert state2.checklist[0].completed_at is not None

    def test_toggle_checklist_item_complete_to_incomplete(self) -> None:
        """Should toggle item from complete to incomplete."""
        state1 = TaskState(
            task_id="task-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            checklist=[
                ChecklistItem(
                    text="Done",
                    completed=True,
                    completed_at=datetime.utcnow(),
                ),
            ],
        )
        state2 = state1.toggle_checklist_item(0)

        assert state2.checklist[0].completed is False
        assert state2.checklist[0].completed_at is None

    def test_toggle_checklist_item_invalid_index(self) -> None:
        """Should raise ValueError for invalid index."""
        state = TaskState(
            task_id="task-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            checklist=[ChecklistItem(text="One item")],
        )
        with pytest.raises(ValueError, match="out of range"):
            state.toggle_checklist_item(5)

    def test_immutability(self) -> None:
        """TaskState should be frozen (immutable)."""
        state = TaskState(
            task_id="task-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        with pytest.raises(Exception):  # ValidationError for frozen model
            state.notes = "Modified"  # type: ignore
