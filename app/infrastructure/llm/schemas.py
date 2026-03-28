from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.models.checklist import ChecklistResponse


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
