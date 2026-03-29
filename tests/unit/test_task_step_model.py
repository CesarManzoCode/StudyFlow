"""
Unit tests for TaskStep domain model.
"""

import pytest
from app.domain.models.task_step import TaskStep, StepDifficulty


class TestStepDifficulty:
    """Test cases for StepDifficulty enum."""

    def test_all_difficulty_levels_defined(self):
        """Test that all difficulty levels are defined."""
        assert StepDifficulty.TRIVIAL.value == "trivial"
        assert StepDifficulty.EASY.value == "easy"
        assert StepDifficulty.MODERATE.value == "moderate"
        assert StepDifficulty.HARD.value == "hard"

    def test_effort_indicator_trivial(self):
        """Test effort indicator for trivial difficulty."""
        assert StepDifficulty.TRIVIAL.effort_indicator == "⚡"

    def test_effort_indicator_easy(self):
        """Test effort indicator for easy difficulty."""
        assert StepDifficulty.EASY.effort_indicator == "✓"

    def test_effort_indicator_moderate(self):
        """Test effort indicator for moderate difficulty."""
        assert StepDifficulty.MODERATE.effort_indicator == "●"

    def test_effort_indicator_hard(self):
        """Test effort indicator for hard difficulty."""
        assert StepDifficulty.HARD.effort_indicator == "⚠"

    def test_time_budget_trivial(self):
        """Test time budget for trivial difficulty."""
        assert StepDifficulty.TRIVIAL.time_budget == "< 1 min"

    def test_time_budget_easy(self):
        """Test time budget for easy difficulty."""
        assert StepDifficulty.EASY.time_budget == "1-5 min"

    def test_time_budget_moderate(self):
        """Test time budget for moderate difficulty."""
        assert StepDifficulty.MODERATE.time_budget == "5-15 min"

    def test_time_budget_hard(self):
        """Test time budget for hard difficulty."""
        assert StepDifficulty.HARD.time_budget == "15+ min"


class TestTaskStep:
    """Test cases for TaskStep model."""

    def test_task_step_creation(self):
        """Test creating a TaskStep."""
        step = TaskStep(
            description="Write introduction",
            estimated_minutes=15,
            difficulty=StepDifficulty.MODERATE,
            is_minimal_first_step=False,
        )
        
        assert step.description == "Write introduction"
        assert step.estimated_minutes == 15
        assert step.difficulty == StepDifficulty.MODERATE
        assert step.is_minimal_first_step is False

    def test_task_step_effort_indicator_property(self):
        """Test task step effort indicator property."""
        step = TaskStep(
            description="Quick task",
            estimated_minutes=1,
            difficulty=StepDifficulty.TRIVIAL,
            is_minimal_first_step=True,
        )
        
        assert step.effort_indicator == "⚡"

    def test_task_step_formatted_time_property(self):
        """Test task step formatted time property."""
        steps = [
            (1, "1 min"),
            (5, "5 min"),
            (15, "15 min"),
            (30, "30 min"),
            (60, "60 min"),
        ]
        
        for minutes, expected_format in steps:
            step = TaskStep(
                description="Test",
                estimated_minutes=minutes,
                difficulty=StepDifficulty.MODERATE,
                is_minimal_first_step=False,
            )
            assert step.formatted_time == expected_format

    def test_task_step_estimated_minutes_validation(self):
        """Test that estimated_minutes is validated."""
        # Valid range: 1-120
        valid_step = TaskStep(
            description="Valid",
            estimated_minutes=60,
            difficulty=StepDifficulty.MODERATE,
            is_minimal_first_step=False,
        )
        assert valid_step.estimated_minutes == 60

    def test_task_step_estimated_minutes_too_low(self):
        """Test that estimated_minutes rejects values < 1."""
        with pytest.raises(ValueError):
            TaskStep(
                description="Invalid",
                estimated_minutes=0,
                difficulty=StepDifficulty.MODERATE,
                is_minimal_first_step=False,
            )

    def test_task_step_estimated_minutes_too_high(self):
        """Test that estimated_minutes rejects values > 120."""
        with pytest.raises(ValueError):
            TaskStep(
                description="Invalid",
                estimated_minutes=121,
                difficulty=StepDifficulty.MODERATE,
                is_minimal_first_step=False,
            )

    def test_task_step_as_minimal_first_step(self):
        """Test task step marked as minimal first step."""
        step = TaskStep(
            description="Open document",
            estimated_minutes=1,
            difficulty=StepDifficulty.TRIVIAL,
            is_minimal_first_step=True,
        )
        
        assert step.is_minimal_first_step is True
        assert step.effort_indicator == "⚡"
        assert step.estimated_minutes == 1

    def test_task_step_json_serialization(self):
        """Test that TaskStep can be serialized to JSON."""
        step = TaskStep(
            description="Write content",
            estimated_minutes=10,
            difficulty=StepDifficulty.MODERATE,
            is_minimal_first_step=False,
        )
        
        json_data = step.model_dump()
        
        assert json_data["description"] == "Write content"
        assert json_data["estimated_minutes"] == 10
        assert json_data["difficulty"] == "moderate"
        assert json_data["is_minimal_first_step"] is False

    def test_task_step_all_difficulties(self):
        """Test TaskStep with all difficulty levels."""
        difficulties = [
            StepDifficulty.TRIVIAL,
            StepDifficulty.EASY,
            StepDifficulty.MODERATE,
            StepDifficulty.HARD,
        ]
        
        for difficulty in difficulties:
            step = TaskStep(
                description="Test step",
                estimated_minutes=5,
                difficulty=difficulty,
                is_minimal_first_step=False,
            )
            
            assert step.difficulty == difficulty
            assert step.difficulty in [
                StepDifficulty.TRIVIAL,
                StepDifficulty.EASY,
                StepDifficulty.MODERATE,
                StepDifficulty.HARD,
            ]

    def test_task_step_description_required(self):
        """Test that description field is required."""
        with pytest.raises(ValueError):
            TaskStep(
                description="",  # Empty description
                estimated_minutes=5,
                difficulty=StepDifficulty.MODERATE,
                is_minimal_first_step=False,
            )

    def test_task_step_boundary_minutes(self):
        """Test boundary values for estimated_minutes."""
        # Minimum valid
        min_step = TaskStep(
            description="Minimal",
            estimated_minutes=1,
            difficulty=StepDifficulty.TRIVIAL,
            is_minimal_first_step=True,
        )
        assert min_step.estimated_minutes == 1
        
        # Maximum valid
        max_step = TaskStep(
            description="Maximal",
            estimated_minutes=120,
            difficulty=StepDifficulty.HARD,
            is_minimal_first_step=False,
        )
        assert max_step.estimated_minutes == 120
