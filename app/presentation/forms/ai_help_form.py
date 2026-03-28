from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AiHelpForm(BaseModel):
    """
    Form model for AI help requests.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    user_question: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional user refinement for the AI prompt.",
    )

    @classmethod
    def from_form(cls, user_question: str | None = None) -> "AiHelpForm":
        """
        Factory method to adapt FastAPI form input.
        """
        normalized = user_question.strip() if user_question else None

        if normalized == "":
            normalized = None

        return cls(user_question=normalized)