"""
Integration tests for AI help enhanced routes.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.domain.models.task_step import EnhancedChecklistResponse, StepDifficulty, TaskStep
from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_container(monkeypatch):
    """Mock the application container."""
    mock_container = MagicMock()
    mock_execute = AsyncMock()
    mock_container.generate_task_help.execute_enhanced = mock_execute
    
    # Patch the container in app state
    app.state.container = mock_container
    return mock_container


class TestEnhancedTaskHelp:
    """Test cases for enhanced AI help endpoint."""

    def test_get_enhanced_help_success(self, client, mock_container):
        """Test successful retrieval of enhanced task help."""
        # Arrange
        task_id = "task-123"
        mock_checklist = EnhancedChecklistResponse(
            summary="Write an introduction",
            deliverable="Introduction section complete",
            steps=[
                TaskStep(
                    description="Open document",
                    estimated_minutes=2,
                    difficulty=StepDifficulty.EASY,
                    is_minimal_first_step=True,
                ),
                TaskStep(
                    description="Write introduction paragraph",
                    estimated_minutes=15,
                    difficulty=StepDifficulty.MODERATE,
                    is_minimal_first_step=False,
                ),
                TaskStep(
                    description="Review introduction",
                    estimated_minutes=5,
                    difficulty=StepDifficulty.EASY,
                    is_minimal_first_step=False,
                ),
            ],
            warnings=[],
            questions_to_clarify=[],
            final_checklist=["Intro done"]
        )
        mock_container.generate_task_help.execute_enhanced.return_value = mock_checklist
        
        # Act
        response = client.post(f"/api/tasks/{task_id}/help/enhanced")
        
        # Assert
        assert response.status_code == 200
        
        data = response.json()
        assert data["summary"] == "Write an introduction"
        assert data["deliverable"] == "Introduction section complete"
        assert len(data["steps"]) == 3
        assert data["total_estimated_minutes"] == 22
        assert data["has_minimal_first_step"] is True
        assert data["minimal_first_step"] is not None

    def test_enhanced_help_with_user_question(self, client, mock_container):
        """Test enhanced help with user question."""
        # Arrange
        task_id = "task-456"
        user_question = "How do I structure this?"
        mock_checklist = EnhancedChecklistResponse(
            summary="Structure guide",
            deliverable="Structure completed",
            steps=[
                TaskStep(
                    description="Read examples",
                    estimated_minutes=6,
                    difficulty=StepDifficulty.EASY,
                    is_minimal_first_step=True,
                ),
                TaskStep(
                    description="Create outline",
                    estimated_minutes=12,
                    difficulty=StepDifficulty.MODERATE,
                    is_minimal_first_step=False,
                ),
            ],
            warnings=[],
            questions_to_clarify=[],
            final_checklist=[]
        )
        mock_container.generate_task_help.execute_enhanced.return_value = mock_checklist
        
        # Act
        response = client.post(
            f"/api/tasks/{task_id}/help/enhanced",
            params={"user_question": user_question}
        )
        
        # Assert
        assert response.status_code == 200
        mock_container.generate_task_help.execute_enhanced.assert_called_once_with(
            task_id=task_id,
            user_question=user_question,
        )

    def test_step_effort_indicators(self, client, mock_container):
        """Test that step difficulty indicators are properly assigned."""
        # Arrange
        mock_checklist = EnhancedChecklistResponse(
            summary="Task",
            deliverable="Done",
            steps=[
                TaskStep(
                    description="Open the file",
                    estimated_minutes=1,
                    difficulty=StepDifficulty.TRIVIAL,
                    is_minimal_first_step=True,
                ),
                TaskStep(
                    description="Write the content",
                    estimated_minutes=12,
                    difficulty=StepDifficulty.MODERATE,
                    is_minimal_first_step=False,
                ),
                TaskStep(
                    description="Review the work",
                    estimated_minutes=4,
                    difficulty=StepDifficulty.EASY,
                    is_minimal_first_step=False,
                ),
            ],
            warnings=[],
            questions_to_clarify=[],
            final_checklist=[]
        )
        mock_container.generate_task_help.execute_enhanced.return_value = mock_checklist
        
        # Act
        response = client.post("/api/tasks/task-789/help/enhanced")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        steps = data["steps"]
        
        # First step (open) should be trivial
        assert steps[0]["difficulty"] == "trivial"
        assert steps[0]["effort_indicator"] == "⚡"
        assert steps[0]["estimated_minutes"] == 1
        assert steps[0]["is_minimal_first_step"] is True
        
        # Second step (write) should be moderate
        assert steps[1]["difficulty"] == "moderate"
        assert steps[1]["estimated_minutes"] > 0
        assert steps[1]["is_minimal_first_step"] is False
        
        # All steps should have formatted_time
        for step in steps:
            assert "min" in step["formatted_time"]

    def test_total_time_calculation(self, client, mock_container):
        """Test that total estimated minutes is calculated correctly."""
        # Arrange
        mock_checklist = EnhancedChecklistResponse(
            summary="Task",
            deliverable="Done",
            steps=[
                TaskStep(
                    description="Click button",
                    estimated_minutes=1,
                    difficulty=StepDifficulty.TRIVIAL,
                    is_minimal_first_step=True,
                ),
                TaskStep(
                    description="Write paragraph",
                    estimated_minutes=10,
                    difficulty=StepDifficulty.MODERATE,
                    is_minimal_first_step=False,
                ),
                TaskStep(
                    description="Save file",
                    estimated_minutes=1,
                    difficulty=StepDifficulty.TRIVIAL,
                    is_minimal_first_step=False,
                ),
            ],
            warnings=[],
            questions_to_clarify=[],
            final_checklist=[]
        )
        mock_container.generate_task_help.execute_enhanced.return_value = mock_checklist
        
        # Act
        response = client.post("/api/tasks/task-time/help/enhanced")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Total should be sum of all steps
        total = data["total_estimated_minutes"]
        assert total == 12

    def test_empty_steps_list(self, client, mock_container):
        """Test handling of empty steps list."""
        # Arrange
        mock_checklist = EnhancedChecklistResponse(
            summary="No steps",
            deliverable="Done",
            steps=[],
            warnings=[],
            questions_to_clarify=[],
            final_checklist=[]
        )
        mock_container.generate_task_help.execute_enhanced.return_value = mock_checklist
        
        # Act
        response = client.post("/api/tasks/task-empty/help/enhanced")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["steps"]) == 0
        assert data["total_estimated_minutes"] == 0
        assert data["has_minimal_first_step"] is False
        assert data["minimal_first_step"] is None

    def test_minimal_first_step_always_first(self, client, mock_container):
        """Test that minimal_first_step is always the first step."""
        # Arrange
        mock_checklist = EnhancedChecklistResponse(
            summary="Multi-step task",
            deliverable="Complete",
            steps=[
                TaskStep(
                    description="Initial setup (trivial)",
                    estimated_minutes=2,
                    difficulty=StepDifficulty.EASY,
                    is_minimal_first_step=True,
                ),
                TaskStep(
                    description="Main work (hard)",
                    estimated_minutes=25,
                    difficulty=StepDifficulty.HARD,
                    is_minimal_first_step=False,
                ),
                TaskStep(
                    description="Final review (easy)",
                    estimated_minutes=6,
                    difficulty=StepDifficulty.EASY,
                    is_minimal_first_step=False,
                ),
            ],
            warnings=[],
            questions_to_clarify=[],
            final_checklist=[]
        )
        mock_container.generate_task_help.execute_enhanced.return_value = mock_checklist
        
        # Act
        response = client.post("/api/tasks/task-multi/help/enhanced")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Minimal first step should be the first step
        minimal_step = data["minimal_first_step"]
        first_step = data["steps"][0]
        
        assert minimal_step["description"] == first_step["description"]
        assert minimal_step["is_minimal_first_step"] is True
        assert first_step["is_minimal_first_step"] is True

    def test_response_model_completeness(self, client, mock_container):
        """Test that response includes all required fields."""
        # Arrange
        mock_checklist = EnhancedChecklistResponse(
            summary="Complete task",
            deliverable="All done",
            steps=[
                TaskStep(
                    description="Step 1",
                    estimated_minutes=3,
                    difficulty=StepDifficulty.EASY,
                    is_minimal_first_step=True,
                ),
                TaskStep(
                    description="Step 2",
                    estimated_minutes=9,
                    difficulty=StepDifficulty.MODERATE,
                    is_minimal_first_step=False,
                ),
            ],
            warnings=["Be careful"],
            questions_to_clarify=["What about X?"],
            final_checklist=["Item 1"]
        )
        mock_container.generate_task_help.execute_enhanced.return_value = mock_checklist
        
        # Act
        response = client.post("/api/tasks/task-full/help/enhanced")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # All required fields present
        assert "summary" in data
        assert "deliverable" in data
        assert "steps" in data
        assert "warnings" in data
        assert "questions_to_clarify" in data
        assert "final_checklist" in data
        assert "total_estimated_minutes" in data
        assert "minimal_first_step" in data
        assert "has_minimal_first_step" in data
        
        # Verify step structure
        for step in data["steps"]:
            assert "description" in step
            assert "estimated_minutes" in step
            assert "difficulty" in step
            assert "is_minimal_first_step" in step
            assert "effort_indicator" in step
            assert "formatted_time" in step
