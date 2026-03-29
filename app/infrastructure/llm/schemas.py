from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.models.checklist import ChecklistResponse
from app.domain.models.task_step import EnhancedChecklistResponse, StepDifficulty, TaskStep


class EnhancedStepPayload(BaseModel):
    """Normalized payload for a single enriched step returned by an LLM."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    description: str = Field(..., min_length=1)
    estimated_minutes: int = Field(default=5, ge=1, le=120)
    difficulty: StepDifficulty = Field(default=StepDifficulty.MODERATE)
    is_minimal_first_step: bool = Field(default=False)


class EnhancedChecklistPayload(BaseModel):
    """
    Infrastructure-level normalized payload for enriched checklist responses.

    This schema is meant for endpoints that need per-step metadata generated
    directly by the LLM (not local heuristics).
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    summary: str = Field(..., min_length=1)
    deliverable: str = Field(..., min_length=1)
    steps: list[EnhancedStepPayload] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    questions_to_clarify: list[str] = Field(default_factory=list)
    final_checklist: list[str] = Field(default_factory=list)

    @field_validator(
        "warnings",
        "questions_to_clarify",
        "final_checklist",
        mode="before",
    )
    @classmethod
    def normalize_string_list(cls, value: object) -> list[str]:
        if value is None:
            return []

        if not isinstance(value, list):
            msg = "Expected a list of strings."
            raise ValueError(msg)

        normalized_items: list[str] = []
        for item in value:
            normalized = str(item).strip()
            if normalized:
                normalized_items.append(normalized)

        return normalized_items

    def to_domain(self) -> EnhancedChecklistResponse:
        """Convert infrastructure payload to enhanced domain model."""
        return EnhancedChecklistResponse(
            summary=self.summary,
            deliverable=self.deliverable,
            steps=[
                TaskStep(
                    description=step.description,
                    estimated_minutes=step.estimated_minutes,
                    difficulty=step.difficulty,
                    is_minimal_first_step=step.is_minimal_first_step,
                )
                for step in self.steps
            ],
            warnings=self.warnings,
            questions_to_clarify=self.questions_to_clarify,
            final_checklist=self.final_checklist,
        )

    @classmethod
    def openai_response_schema(cls) -> dict[str, object]:
        """Return strict JSON schema for OpenAI structured outputs."""
        schema = cls.model_json_schema()
        properties = schema.get("properties")

        if isinstance(properties, dict):
            schema["required"] = list(properties.keys())

        schema["additionalProperties"] = False
        return schema


def fallback_enhanced_from_checklist(payload: ChecklistResponse) -> EnhancedChecklistResponse:
    """
    Conservative fallback when provider cannot return step metadata.

    Keeps behavior deterministic while still preferring LLM-native metadata when
    available.
    """
    steps: list[TaskStep] = []
    for index, raw_step in enumerate(payload.steps):
        difficulty = StepDifficulty.EASY if index == 0 else StepDifficulty.MODERATE
        minutes = 3 if index == 0 else 8
        steps.append(
            TaskStep(
                description=raw_step,
                estimated_minutes=minutes,
                difficulty=difficulty,
                is_minimal_first_step=index == 0,
            )
        )

    return EnhancedChecklistResponse(
        summary=payload.summary,
        deliverable=payload.deliverable,
        steps=steps,
        warnings=payload.warnings,
        questions_to_clarify=payload.questions_to_clarify,
        final_checklist=payload.final_checklist,
    )


class ChecklistPayload(BaseModel):
    """
    Infrastructure-level normalized payload for LLM checklist responses.

    This model is used to validate and normalize provider output before
    converting it into the domain-level ChecklistResponse.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    summary: str = Field(..., min_length=1)
    deliverable: str = Field(..., min_length=1)
    steps: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    questions_to_clarify: list[str] = Field(default_factory=list)
    final_checklist: list[str] = Field(default_factory=list)

    @field_validator(
        "steps",
        "warnings",
        "questions_to_clarify",
        "final_checklist",
        mode="before",
    )
    @classmethod
    def normalize_string_list(cls, value: object) -> list[str]:
        """
        Normalize provider list-like output into a clean list of strings.

        Accepts:
        - None -> []
        - list[str | other] -> cleaned list[str]

        Raises:
            ValueError: if the value is not list-like.
        """
        if value is None:
            return []

        if not isinstance(value, list):
            msg = "Expected a list of strings."
            raise ValueError(msg)

        normalized_items: list[str] = []
        for item in value:
            normalized = str(item).strip()
            if normalized:
                normalized_items.append(normalized)

        return normalized_items

    def to_domain(self) -> ChecklistResponse:
        """
        Convert the infrastructure payload into the domain model.
        """
        return ChecklistResponse(
            summary=self.summary,
            deliverable=self.deliverable,
            steps=self.steps,
            warnings=self.warnings,
            questions_to_clarify=self.questions_to_clarify,
            final_checklist=self.final_checklist,
        )

    @classmethod
    def openai_response_schema(cls) -> dict[str, object]:
        """
        Return a strict JSON schema compatible with OpenAI structured outputs.
        """
        schema = cls.model_json_schema()
        properties = schema.get("properties")

        if isinstance(properties, dict):
            schema["required"] = list(properties.keys())

        schema["additionalProperties"] = False
        return schema
