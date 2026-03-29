"""
Integration tests for day planning routes.
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import replace

import pytest
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient

from app.infrastructure.factories import build_app_container, AppContainer
from app.infrastructure.persistence.persistent_state_store import (
    PersistentTaskStateStore,
)
from app.presentation.routes.planning import router as planning_router


@pytest.fixture
def client() -> TestClient:
    """Create an isolated test client per test."""
    import shutil

    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Create FastAPI app
        app = FastAPI(debug=True)

        # Create a minimal static files mount
        static_dir = temp_dir / "static"
        static_dir.mkdir(exist_ok=True)
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

        # Create ISOLATED state store
        test_store = PersistentTaskStateStore(data_dir=temp_dir)

        # Create and attach container to app state
        container = build_app_container()
        container = replace(container, state_repository=test_store)
        app.state.container = container

        # Include router
        app.include_router(planning_router)

        yield TestClient(app)

        # Restore original
        pass

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


class TestPlanMyDayEndpoint:
    """Test GET /api/plan/my-day endpoint."""

    def test_plan_my_day_endpoint_exists(self, client: TestClient) -> None:
        """Should respond to /api/plan/my-day endpoint."""
        response = client.get("/api/plan/my-day")
        assert response.status_code == 200

    def test_plan_my_day_returns_day_plan_model(
        self, client: TestClient
    ) -> None:
        """Should return DayPlanResponse model."""
        response = client.get("/api/plan/my-day")
        assert response.status_code == 200

        data = response.json()

        # Check required fields
        assert "created_at" in data
        assert "planned_for_date" in data
        assert "planned_tasks" in data
        assert "total_minutes" in data
        assert "total_hours" in data
        assert "is_feasible" in data
        assert "cognitive_balance" in data
        assert "pending_tasks_count" in data

    def test_plan_my_day_with_no_tasks(self, client: TestClient) -> None:
        """Should return empty plan when no tasks."""
        response = client.get("/api/plan/my-day")
        assert response.status_code == 200

        data = response.json()
        assert len(data["planned_tasks"]) == 0
        assert data["total_minutes"] == 0
        assert data["is_feasible"] is True

    def test_planned_task_response_fields(self, client: TestClient) -> None:
        """Should include all planned task fields in response."""
        response = client.get("/api/plan/my-day")
        data = response.json()

        # Even with no tasks, structure should be present
        assert "planned_tasks" in data
        assert isinstance(data["planned_tasks"], list)

    def test_day_plan_is_feasible_with_reasonable_load(
        self, client: TestClient
    ) -> None:
        """Should mark plan as feasible when total is within 8 hours."""
        response = client.get("/api/plan/my-day")
        data = response.json()

        # Default demonstration should be feasible
        assert data["is_feasible"] is True

    def test_cognitive_balance_for_empty_plan(self, client: TestClient) -> None:
        """Should return valid cognitive balance for empty plan."""
        response = client.get("/api/plan/my-day")
        data = response.json()

        # Should have a cognitive_balance value
        assert data["cognitive_balance"] in ["balanced", "heavy"]

    def test_total_hours_calculation(self, client: TestClient) -> None:
        """Should calculate total hours correctly."""
        response = client.get("/api/plan/my-day")
        data = response.json()

        total_minutes = data["total_minutes"]
        total_hours = data["total_hours"]

        # Verify relationship
        expected_hours = round(total_minutes / 60, 1)
        assert total_hours == expected_hours

    def test_pending_tasks_count(self, client: TestClient) -> None:
        """Should track tasks not included in today's plan."""
        response = client.get("/api/plan/my-day")
        data = response.json()

        # Should have a pending_tasks_count
        assert "pending_tasks_count" in data
        assert data["pending_tasks_count"] >= 0


class TestPlanningResponseFormat:
    """Test the format and structure of planning responses."""

    def test_response_includes_iso_datetime_strings(
        self, client: TestClient
    ) -> None:
        """Should return datetime fields as ISO strings."""
        response = client.get("/api/plan/my-day")
        data = response.json()

        # ISO datetime format should be parseable
        assert isinstance(data["created_at"], str)
        assert isinstance(data["planned_for_date"], str)

        # Should be parseable as ISO
        datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        datetime.fromisoformat(data["planned_for_date"].replace("Z", "+00:00"))

    def test_planned_task_fields(self, client: TestClient) -> None:
        """Should include all required task fields."""
        # This test just verifies the structure, even with 0 tasks
        response = client.get("/api/plan/my-day")
        data = response.json()

        # planned_tasks should be an empty list for demo
        assert isinstance(data["planned_tasks"], list)

    def test_numeric_fields_are_numbers(self, client: TestClient) -> None:
        """Should return numeric fields as numbers, not strings."""
        response = client.get("/api/plan/my-day")
        data = response.json()

        assert isinstance(data["total_minutes"], int)
        assert isinstance(data["total_hours"], (int, float))
        assert isinstance(data["pending_tasks_count"], int)

    def test_boolean_fields_are_booleans(self, client: TestClient) -> None:
        """Should return boolean fields as actual booleans."""
        response = client.get("/api/plan/my-day")
        data = response.json()

        assert isinstance(data["is_feasible"], bool)

    def test_string_fields_are_strings(self, client: TestClient) -> None:
        """Should return string fields as strings."""
        response = client.get("/api/plan/my-day")
        data = response.json()

        assert isinstance(data["cognitive_balance"], str)
        assert data["cognitive_balance"] in ["balanced", "heavy"]
