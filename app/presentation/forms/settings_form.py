from __future__ import annotations

from typing import Annotated

from fastapi import Form
from pydantic import BaseModel, ConfigDict


class SettingsForm(BaseModel):
    """
    Form model for application settings submission.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    moodle_base_url: str
    moodle_username: str
    moodle_password: str
    llm_provider: str
    llm_model: str
    llm_api_key: str | None = None
    llm_base_url: str | None = None

    @classmethod
    def from_form(
        cls,
        moodle_base_url: Annotated[str, Form(...)],
        moodle_username: Annotated[str, Form(...)],
        moodle_password: Annotated[str, Form(...)],
        llm_provider: Annotated[str, Form(...)],
        llm_model: Annotated[str, Form(...)],
        llm_api_key: Annotated[str | None, Form()] = None,
        llm_base_url: Annotated[str | None, Form()] = None,
    ) -> "SettingsForm":
        """
        Factory method to adapt FastAPI form input.
        """

        def normalize(value: str | None) -> str | None:
            if value is None:
                return None
            value = value.strip()
            return value or None

        return cls(
            moodle_base_url=normalize(moodle_base_url) or "",
            moodle_username=normalize(moodle_username) or "",
            moodle_password=normalize(moodle_password) or "",
            llm_provider=normalize(llm_provider) or "",
            llm_model=normalize(llm_model) or "",
            llm_api_key=normalize(llm_api_key),
            llm_base_url=normalize(llm_base_url),
        )
