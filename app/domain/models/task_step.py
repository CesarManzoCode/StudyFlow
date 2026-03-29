from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class StepDifficulty(str, Enum):
    """Difficulty level of a task step."""
    TRIVIAL = "trivial"    # < 1 min, no thinking
    EASY = "easy"          # 1-5 min, minimal thinking
    MODERATE = "moderate"  # 5-15 min, some thinking
    HARD = "hard"          # 15+ min, deep thinking

    @property
    def effort_indicator(self) -> str:
        """Visual indicator of effort level."""
        indicators = {
            "trivial": "⚡",
            "easy": "✓",
            "moderate": "●",
            "hard": "⚠",
        }
        return indicators.get(self.value, "?")

    @property
    def time_budget(self) -> str:
        """Recommended time budget for this difficulty level."""
        budgets = {
            "trivial": "< 1 min",
            "easy": "1-5 min",
            "moderate": "5-15 min",
            "hard": "15+ min",
        }
        return budgets.get(self.value, "unknown")
class TaskStep(BaseModel):
    """
    A single step in a task with time estimate and difficulty.
    
    This model represents an actionable step with concrete effort metrics
    to help users understand exactly what they're signing up for.
    """

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
    )

    description: str = Field(..., min_length=1, description="What to do")
    estimated_minutes: int = Field(
        default=5,
        ge=1,
        le=120,
        description="Time estimate in minutes"
    )
    difficulty: StepDifficulty = Field(
        default=StepDifficulty.EASY,
        description="Effort level: trivial, easy, moderate, hard"
    )
    is_minimal_first_step: bool = Field(
        default=False,
        description="Is this the smallest possible first step?"
    )

    @property
    def effort_indicator(self) -> str:
        """Return a visual indicator of effort."""
        indicators = {
            StepDifficulty.TRIVIAL: "⚡",
            StepDifficulty.EASY: "✓",
            StepDifficulty.MODERATE: "●",
            StepDifficulty.HARD: "⚠",
        }
        return indicators.get(self.difficulty, "?")

    @property
    def formatted_time(self) -> str:
        """Return formatted time (e.g., '5 min')."""
        if self.estimated_minutes == 1:
            return "1 min"
        return f"{self.estimated_minutes} min"


class EnhancedChecklistResponse(BaseModel):
    """
    Enhanced AI assistance output with detailed step information.
    
    This extends ChecklistResponse with rich step metadata to help users
    understand exactly what they need to do and how long it will take.
    """

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
    )

    summary: str = Field(..., min_length=1, description="Brief task summary")
    deliverable: str = Field(..., min_length=1, description="What you'll produce")

    steps: list[TaskStep] = Field(
        default_factory=list,
        description="Ordered steps with time and difficulty"
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Important gotchas or prerequisites"
    )
    questions_to_clarify: list[str] = Field(
        default_factory=list,
        description="Questions to ask if unclear"
    )
    final_checklist: list[str] = Field(
        default_factory=list,
        description="Final verification items"
    )

    @property
    def total_estimated_minutes(self) -> int:
        """Sum of all step time estimates."""
        return sum(s.estimated_minutes for s in self.steps)

    @property
    def minimal_first_step(self) -> TaskStep | None:
        """Get the first minimal step if marked."""
        return next(
            (s for s in self.steps if s.is_minimal_first_step),
            None
        )

    @property
    def has_minimal_first_step(self) -> bool:
        """Check if a minimal first step is defined."""
        return self.minimal_first_step is not None
