from pydantic import BaseModel, ConfigDict, Field


class ChecklistResponse(BaseModel):
    """
    Structured AI assistance output for a selected task.

    This model represents the normalized response returned by any LLM provider
    after generating clear, actionable guidance for completing an assignment.
    """

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
    )

    summary: str = Field(..., min_length=1)
    deliverable: str = Field(..., min_length=1)

    steps: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    questions_to_clarify: list[str] = Field(default_factory=list)
    final_checklist: list[str] = Field(default_factory=list)