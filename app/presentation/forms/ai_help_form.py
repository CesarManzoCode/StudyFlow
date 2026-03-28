from __future__ import annotations

from typing import Annotated

from fastapi import Form
from pydantic import BaseModel, ConfigDict


class AiHelpForm(BaseModel):
    """
    Form model for AI help requests.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    user_question: str | None = None

    @classmethod
    def from_form(
        cls,
        user_question: Annotated[str | None, Form()] = None,
    ) -> "AiHelpForm":
        """
        Factory method to adapt FastAPI form input.
        """
        normalized = user_question.strip() if user_question else None

        if normalized == "":
            normalized = None

        return cls(user_question=normalized)
