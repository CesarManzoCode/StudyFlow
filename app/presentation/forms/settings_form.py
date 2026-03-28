from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SettingsForm(BaseModel):
    """
    Form model for application settings submission.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    # Moodle
    moodle_base_url: str = Field(..., min_length=1)
    moodle_username: str = Field(..., min_length=1)
    moodle_password: str = Field(..., min_length=1)

    # LLM
    llm_provider: str = Field(..., min_length=1)
    llm_model: str = Field(..., min_length=1)

    llm_api_key: str | None = Field(default=None)
    llm_base_url: str | None = Field(default=None)

    @classmethod
    def from_form(
        cls,
        moodle_base_url: str,
        moodle_username: str,
        moodle_password: str,
        llm_provider: str,
        llm_model: str,
        llm_api_key: str | None = None,
        llm_base_url: str | None = None,
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