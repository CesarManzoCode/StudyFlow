"""
Unit tests for PersistentTaskStateStore repository.
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from app.domain.models.task_state import ChecklistItem, TaskState
from app.infrastructure.persistence.persistent_state_store import (
    PersistentTaskStateStore,
)


@pytest.fixture
def temp_data_dir() -> Path:
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def store(temp_data_dir: Path) -> PersistentTaskStateStore:
    """Create a store with temporary data directory."""
    return PersistentTaskStateStore(data_dir=temp_data_dir)


class TestPersistentTaskStateStore:
    """Test PersistentTaskStateStore."""

    @pytest.mark.asyncio
    async def test_save_and_retrieve(self, store: PersistentTaskStateStore) -> None:
        """Should save and retrieve task state."""
        state = TaskState(
            task_id="task-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            notes="Review requirements",
        )
        await store.save(state)

        retrieved = await store.get_by_task_id("task-123")
        assert retrieved is not None
        assert retrieved.task_id == "task-123"
        assert retrieved.notes == "Review requirements"

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(
        self, store: PersistentTaskStateStore
    ) -> None:
        """Should return None for nonexistent task."""
        result = await store.get_by_task_id("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_existing_state(self, store: PersistentTaskStateStore) -> None:
        """Should update existing task state."""
        state1 = TaskState(
            task_id="task-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            notes="Version 1",
        )
        await store.save(state1)

        state2 = state1.with_notes("Version 2")
        await store.save(state2)

        retrieved = await store.get_by_task_id("task-123")
        assert retrieved is not None
        assert retrieved.notes == "Version 2"

    @pytest.mark.asyncio
    async def test_save_with_checklist(self, store: PersistentTaskStateStore) -> None:
        """Should save and retrieve state with checklist."""
        state = TaskState(
            task_id="task-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            checklist=[
                ChecklistItem(text="Step 1", completed=True),
                ChecklistItem(text="Step 2", completed=False),
            ],
        )
        await store.save(state)

        retrieved = await store.get_by_task_id("task-123")
        assert retrieved is not None
        assert len(retrieved.checklist) == 2
        assert retrieved.checklist[0].completed is True
        assert retrieved.checklist[1].completed is False

    @pytest.mark.asyncio
    async def test_get_all_empty(self, store: PersistentTaskStateStore) -> None:
        """Should return empty dict when no states exist."""
        all_states = await store.get_all()
        assert all_states == {}

    @pytest.mark.asyncio
    async def test_get_all_multiple(self, store: PersistentTaskStateStore) -> None:
        """Should retrieve all stored task states."""
        state1 = TaskState(
            task_id="task-1",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            notes="Note 1",
        )
        state2 = TaskState(
            task_id="task-2",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            notes="Note 2",
        )
        await store.save(state1)
        await store.save(state2)

        all_states = await store.get_all()
        assert len(all_states) == 2
        assert all_states["task-1"].notes == "Note 1"
        assert all_states["task-2"].notes == "Note 2"

    @pytest.mark.asyncio
    async def test_delete_existing(self, store: PersistentTaskStateStore) -> None:
        """Should delete existing task state."""
        state = TaskState(
            task_id="task-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        await store.save(state)

        result = await store.delete("task-123")
        assert result is True

        retrieved = await store.get_by_task_id("task-123")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, store: PersistentTaskStateStore) -> None:
        """Should return False when deleting nonexistent state."""
        result = await store.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_clear_all(self, store: PersistentTaskStateStore) -> None:
        """Should clear all task states."""
        state1 = TaskState(
            task_id="task-1",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        state2 = TaskState(
            task_id="task-2",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        await store.save(state1)
        await store.save(state2)

        await store.clear_all()

        all_states = await store.get_all()
        assert all_states == {}

    @pytest.mark.asyncio
    async def test_state_file_persistence(
        self, temp_data_dir: Path
    ) -> None:
        """Should persist state to file system."""
        store1 = PersistentTaskStateStore(data_dir=temp_data_dir)
        state = TaskState(
            task_id="task-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            notes="Persist me",
        )
        await store1.save(state)

        # New store instance should read from same file
        store2 = PersistentTaskStateStore(data_dir=temp_data_dir)
        retrieved = await store2.get_by_task_id("task-123")
        assert retrieved is not None
        assert retrieved.notes == "Persist me"
