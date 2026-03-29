"""
Unit tests for task state use cases.
"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.application.use_cases.manage_task_state import (
    GetTaskStateUseCase,
    RecordAIInteractionUseCase,
    ToggleChecklistItemUseCase,
    UpdateTaskChecklistUseCase,
    UpdateTaskNotesUseCase,
)
from app.domain.models.task_state import AIInteraction, ChecklistItem, TaskState


class TestGetTaskStateUseCase:
    """Test GetTaskStateUseCase."""

    @pytest.mark.asyncio
    async def test_get_existing_state(self) -> None:
        """Should retrieve existing task state."""
        state = TaskState(
            task_id="task-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            notes="Test note",
        )
        repo = AsyncMock()
        repo.get_by_task_id.return_value = state

        use_case = GetTaskStateUseCase(state_repo=repo)
        result = await use_case.execute(task_id="task-123")

        assert result == state
        repo.get_by_task_id.assert_called_once_with("task-123")

    @pytest.mark.asyncio
    async def test_get_nonexistent_state(self) -> None:
        """Should return None for nonexistent state."""
        repo = AsyncMock()
        repo.get_by_task_id.return_value = None

        use_case = GetTaskStateUseCase(state_repo=repo)
        result = await use_case.execute(task_id="task-123")

        assert result is None


class TestUpdateTaskNotesUseCase:
    """Test UpdateTaskNotesUseCase."""

    @pytest.mark.asyncio
    async def test_create_new_state_with_notes(self) -> None:
        """Should create new state when it doesn't exist."""
        repo = AsyncMock()
        repo.get_by_task_id.return_value = None

        use_case = UpdateTaskNotesUseCase(state_repo=repo)
        result = await use_case.execute(task_id="task-123", notes="New note")

        assert result.task_id == "task-123"
        assert result.notes == "New note"
        repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_existing_state_notes(self) -> None:
        """Should update notes of existing state."""
        state = TaskState(
            task_id="task-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            notes="Old note",
        )
        repo = AsyncMock()
        repo.get_by_task_id.return_value = state

        use_case = UpdateTaskNotesUseCase(state_repo=repo)
        result = await use_case.execute(task_id="task-123", notes="Updated note")

        assert result.notes == "Updated note"
        assert result.task_id == "task-123"
        repo.save.assert_called_once()


class TestUpdateTaskChecklistUseCase:
    """Test UpdateTaskChecklistUseCase."""

    @pytest.mark.asyncio
    async def test_create_checklist_for_new_state(self) -> None:
        """Should create state with checklist."""
        repo = AsyncMock()
        repo.get_by_task_id.return_value = None

        use_case = UpdateTaskChecklistUseCase(state_repo=repo)
        items = [
            {"text": "Step 1", "completed": False},
            {"text": "Step 2", "completed": True},
        ]
        result = await use_case.execute(task_id="task-123", checklist_items=items)

        assert result.task_id == "task-123"
        assert len(result.checklist) == 2
        assert result.checklist[0].text == "Step 1"
        assert result.checklist[1].completed is True

    @pytest.mark.asyncio
    async def test_update_existing_checklist(self) -> None:
        """Should replace checklist of existing state."""
        state = TaskState(
            task_id="task-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            checklist=[ChecklistItem(text="Old item")],
        )
        repo = AsyncMock()
        repo.get_by_task_id.return_value = state

        use_case = UpdateTaskChecklistUseCase(state_repo=repo)
        items = [{"text": "New item 1"}, {"text": "New item 2"}]
        result = await use_case.execute(task_id="task-123", checklist_items=items)

        assert len(result.checklist) == 2
        assert result.checklist[0].text == "New item 1"


class TestToggleChecklistItemUseCase:
    """Test ToggleChecklistItemUseCase."""

    @pytest.mark.asyncio
    async def test_toggle_item_success(self) -> None:
        """Should toggle checklist item."""
        state = TaskState(
            task_id="task-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            checklist=[
                ChecklistItem(text="Item 1", completed=False),
                ChecklistItem(text="Item 2", completed=True),
            ],
        )
        repo = AsyncMock()
        repo.get_by_task_id.return_value = state

        use_case = ToggleChecklistItemUseCase(state_repo=repo)
        result = await use_case.execute(task_id="task-123", item_index=0)

        assert result.checklist[0].completed is True
        assert result.checklist[0].completed_at is not None

    @pytest.mark.asyncio
    async def test_toggle_nonexistent_state_raises(self) -> None:
        """Should raise ValueError if state doesn't exist."""
        repo = AsyncMock()
        repo.get_by_task_id.return_value = None

        use_case = ToggleChecklistItemUseCase(state_repo=repo)

        with pytest.raises(ValueError, match="No task state exists"):
            await use_case.execute(task_id="task-123", item_index=0)

    @pytest.mark.asyncio
    async def test_toggle_invalid_index_raises(self) -> None:
        """Should raise ValueError for invalid index."""
        state = TaskState(
            task_id="task-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            checklist=[ChecklistItem(text="Only item")],
        )
        repo = AsyncMock()
        repo.get_by_task_id.return_value = state

        use_case = ToggleChecklistItemUseCase(state_repo=repo)

        with pytest.raises(ValueError, match="out of range"):
            await use_case.execute(task_id="task-123", item_index=5)


class TestRecordAIInteractionUseCase:
    """Test RecordAIInteractionUseCase."""

    @pytest.mark.asyncio
    async def test_record_interaction_creates_state(self) -> None:
        """Should create state with interaction."""
        repo = AsyncMock()
        repo.get_by_task_id.return_value = None

        use_case = RecordAIInteractionUseCase(state_repo=repo)
        result = await use_case.execute(
            task_id="task-123",
            interaction_id="ai-001",
            question="How to solve?",
            response="Follow these steps...",
        )

        assert result.task_id == "task-123"
        assert len(result.ai_interactions) == 1
        assert result.ai_interactions[0].question == "How to solve?"
        assert result.ai_interactions[0].response == "Follow these steps..."

    @pytest.mark.asyncio
    async def test_record_interaction_appends_to_existing(self) -> None:
        """Should append interaction to existing state."""
        existing_interaction = AIInteraction(
            interaction_id="ai-001",
            timestamp=datetime.utcnow(),
            question="First question",
        )
        state = TaskState(
            task_id="task-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            ai_interactions=[existing_interaction],
        )
        repo = AsyncMock()
        repo.get_by_task_id.return_value = state

        use_case = RecordAIInteractionUseCase(state_repo=repo)
        result = await use_case.execute(
            task_id="task-123",
            interaction_id="ai-002",
            question="Second question",
        )

        assert len(result.ai_interactions) == 2
        assert result.ai_interactions[0].question == "First question"
        assert result.ai_interactions[1].question == "Second question"

    @pytest.mark.asyncio
    async def test_record_interaction_with_metadata(self) -> None:
        """Should store interaction metadata."""
        repo = AsyncMock()
        repo.get_by_task_id.return_value = None
        metadata = {"model": "gpt-4", "tokens": 100}

        use_case = RecordAIInteractionUseCase(state_repo=repo)
        result = await use_case.execute(
            task_id="task-123",
            interaction_id="ai-001",
            question="Test?",
            metadata=metadata,
        )

        assert result.ai_interactions[0].metadata == metadata
