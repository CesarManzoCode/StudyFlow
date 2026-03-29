"""
Integration tests for task state routes.
"""

import json
import tempfile  
from pathlib import Path
from unittest.mock import AsyncMock
import uuid

import pytest
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient

from app.config import Settings
from app.infrastructure.factories import build_app_container, AppContainer
from app.infrastructure.persistence.persistent_state_store import (
    PersistentTaskStateStore,
)
from app.presentation.routes.task_state import router as task_state_router


@pytest.fixture
def client() -> TestClient:
    """Create an isolated test client per test."""
    import shutil
    from dataclasses import replace
    from app.presentation.routes.task_state import _get_container
    
    # Use context manager for proper cleanup
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir)
        
        # Create FastAPI app
        app = FastAPI(debug=True)

        # Create a minimal static files mount
        static_dir = temp_dir / "static"
        static_dir.mkdir(exist_ok=True)
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

        # Create ISOLATED state store
        test_store = PersistentTaskStateStore(data_dir=temp_dir)

        # Create inline container with test store
        def get_isolated_container() -> AppContainer:
            """Returns a container with the isolated test store."""
            container = build_app_container()
            return replace(container, state_repository=test_store)

        # Use FastAPI's dependency_overrides instead of monkeypatching
        app.dependency_overrides[_get_container] = get_isolated_container

        # Include router
        app.include_router(task_state_router)

        yield TestClient(app)

        # Clean up overrides
        app.dependency_overrides.clear()


class TestTaskStateGETEndpoint:
    """Test GET /api/task-state/{task_id}."""

    def test_get_nonexistent_state(self, client: TestClient) -> None:
        """Should return None for nonexistent task."""
        response = client.get("/api/task-state/task-999")
        assert response.status_code == 200
        assert response.json() is None

    def test_get_existing_state(self, client: TestClient) -> None:
        """Should return existing task state."""
        # First create a state
        request_data = {"notes": "Test note"}
        response = client.patch(
            "/api/task-state/task-123/notes",
            json=request_data,
        )
        assert response.status_code == 200

        # Then retrieve it
        response = client.get("/api/task-state/task-123")
        assert response.status_code == 200
        state = response.json()
        assert state is not None
        assert state["task_id"] == "task-123"
        assert state["notes"] == "Test note"


class TestTaskStateNotesEndpoint:
    """Test PATCH /api/task-state/{task_id}/notes."""

    def test_create_notes_for_new_task(self, client: TestClient) -> None:
        """Should create state with notes."""
        request_data = {"notes": "New task notes"}
        response = client.patch(
            "/api/task-state/task-123/notes",
            json=request_data,
        )
        assert response.status_code == 200
        result = response.json()
        assert result["task_id"] == "task-123"
        assert result["completion_rate"] == 0.0

    def test_update_existing_notes(self, client: TestClient) -> None:
        """Should update existing notes."""
        # Create
        client.patch(
            "/api/task-state/task-123/notes",
            json={"notes": "First note"},
        )

        # Update
        response = client.patch(
            "/api/task-state/task-123/notes",
            json={"notes": "Updated note"},
        )
        assert response.status_code == 200

        # Verify
        response = client.get("/api/task-state/task-123")
        assert response.json()["notes"] == "Updated note"


class TestTaskStateChecklistEndpoint:
    """Test PATCH /api/task-state/{task_id}/checklist."""

    def test_create_checklist(self, client: TestClient) -> None:
        """Should create state with checklist."""
        request_data = {
            "checklist": [
                {"text": "Item 1", "completed": False},
                {"text": "Item 2", "completed": True},
            ]
        }
        response = client.patch(
            "/api/task-state/task-123/checklist",
            json=request_data,
        )
        assert response.status_code == 200
        result = response.json()
        assert result["task_id"] == "task-123"
        assert result["completion_rate"] == 50.0

    def test_update_checklist(self, client: TestClient) -> None:
        """Should replace existing checklist."""
        # Create
        client.patch(
            "/api/task-state/task-123/checklist",
            json={
                "checklist": [
                    {"text": "Old item"},
                ]
            },
        )

        # Update
        response = client.patch(
            "/api/task-state/task-123/checklist",
            json={
                "checklist": [
                    {"text": "New item 1"},
                    {"text": "New item 2"},
                ]
            },
        )
        assert response.status_code == 200

        # Verify
        response = client.get("/api/task-state/task-123")
        checklist = response.json()["checklist"]
        assert len(checklist) == 2
        assert checklist[0]["text"] == "New item 1"

    def test_empty_checklist(self, client: TestClient) -> None:
        """Should allow empty checklist."""
        response = client.patch(
            "/api/task-state/task-123/checklist",
            json={"checklist": []},
        )
        assert response.status_code == 200
        assert response.json()["completion_rate"] == 0.0


class TestToggleChecklistItemEndpoint:
    """Test PATCH /api/task-state/{task_id}/checklist/{item_index}/toggle."""

    def test_toggle_item_success(self, client: TestClient) -> None:
        """Should toggle checklist item."""
        # Create checklist
        client.patch(
            "/api/task-state/task-123/checklist",
            json={
                "checklist": [
                    {"text": "Item 1", "completed": False},
                    {"text": "Item 2", "completed": False},
                ]
            },
        )

        # Toggle first item
        response = client.patch("/api/task-state/task-123/checklist/0/toggle")
        assert response.status_code == 200
        assert response.json()["completion_rate"] == 50.0

        # Verify
        response = client.get("/api/task-state/task-123")
        assert response.json()["checklist"][0]["completed"] is True

    def test_toggle_nonexistent_state_returns_404(
        self, client: TestClient
    ) -> None:
        """Should return 404 if task state doesn't exist."""
        response = client.patch("/api/task-state/task-999/checklist/0/toggle")
        assert response.status_code == 404

    def test_toggle_invalid_index_returns_422(self, client: TestClient) -> None:
        """Should return 422 for invalid index in URL."""
        client.patch(
            "/api/task-state/task-123/checklist",
            json={"checklist": [{"text": "Only one"}]},
        )

        # Try to toggle index that doesn't exist
        # FastAPI will attempt the toggle but the domain will catch it
        response = client.patch("/api/task-state/task-123/checklist/99/toggle")
        # Could be 404 or 422 depending on validation
        assert response.status_code in (404, 422)


class TestRecordInteractionEndpoint:
    """Test POST /api/task-state/{task_id}/interactions."""

    def test_record_interaction(self, client: TestClient) -> None:
        """Should record AI interaction."""
        request_data = {
            "interaction_id": "ai-001",
            "question": "How to approach this?",
            "response": "Here are the steps...",
        }
        response = client.post(
            "/api/task-state/task-123/interactions",
            json=request_data,
        )
        assert response.status_code == 200
        result = response.json()
        assert result["task_id"] == "task-123"

    def test_record_multiple_interactions(self, client: TestClient, task_id: str) -> None:
        """Should record multiple interactions."""
        # First interaction
        client.post(
            f"/api/task-state/{task_id}/interactions",
            json={
                "interaction_id": "ai-001",
                "question": "Q1?",
                "response": "A1",
            },
        )

        # Second interaction
        response = client.post(
            f"/api/task-state/{task_id}/interactions",
            json={
                "interaction_id": "ai-002",
                "question": "Q2?",
                "response": "A2",
            },
        )
        assert response.status_code == 200

        # Verify both are stored
        response = client.get(f"/api/task-state/{task_id}")
        interactions = response.json()["ai_interactions"]
        assert len(interactions) == 2
        assert interactions[0]["question"] == "Q1?"
        assert interactions[1]["question"] == "Q2?"

    def test_record_interaction_with_metadata(self, client: TestClient, task_id: str) -> None:
        """Should record interaction with metadata."""
        request_data = {
            "interaction_id": "ai-001",
            "question": "Help?",
            "metadata": {"model": "gpt-4", "tokens_used": 150},
        }
        response = client.post(
            f"/api/task-state/{task_id}/interactions",
            json=request_data,
        )
        assert response.status_code == 200

        # Verify metadata is stored
        response = client.get(f"/api/task-state/{task_id}")
        interaction = response.json()["ai_interactions"][0]
        assert interaction["metadata"]["model"] == "gpt-4"


class TestFullWorkflow:
    """Test a complete workflow of task state operations."""

    def test_complete_task_state_lifecycle(self, client: TestClient, task_id: str) -> None:
        """Should manage complete task state lifecycle."""
        
        # 1. Create state with notes
        response = client.patch(
            f"/api/task-state/{task_id}/notes",
            json={"notes": "Start working on assignment"},
        )
        assert response.status_code == 200

        # 2. Add checklist
        response = client.patch(
            f"/api/task-state/{task_id}/checklist",
            json={
                "checklist": [
                    {"text": "Read requirements"},
                    {"text": "Write outline"},
                    {"text": "Draft content"},
                ]
            },
        )
        assert response.status_code == 200
        assert response.json()["completion_rate"] == 0.0

        # 3. Toggle first item
        response = client.patch(
            f"/api/task-state/{task_id}/checklist/0/toggle"
        )
        assert response.json()["completion_rate"] == pytest.approx(33.33, rel=0.01)

        # 4. Record AI interaction
        response = client.post(
            f"/api/task-state/{task_id}/interactions",
            json={
                "interaction_id": "ai-001",
                "question": "How should I structure this?",
                "response": "Use the following structure...",
            },
        )
        assert response.status_code == 200

        # 5. Retrieve final state
        response = client.get(f"/api/task-state/{task_id}")
        assert response.status_code == 200
        final_state = response.json()
        assert final_state["notes"] == "Start working on assignment"
        assert len(final_state["checklist"]) == 3
        assert len(final_state["ai_interactions"]) == 1
        assert final_state["checklist"][0]["completed"] is True


@pytest.fixture
def task_id() -> str:
    """Generate a unique task ID per test."""
    return f"task-{uuid.uuid4().hex[:8]}"
