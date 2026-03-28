from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MoodleSettings(BaseModel):
    base_url: str
    username: str
    password: str
    headless: bool = True


class LlmSettings(BaseModel):
    provider: Literal["ollama", "openai", "groq", "anthropic"]

    # comunes
    model: str

    # opcionales por provider
    base_url: str | None = None
    api_key: str | None = None


class AppSettings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Moodle ---
    moodle_base_url: str = Field(..., alias="MOODLE_BASE_URL")
    moodle_username: str = Field(..., alias="MOODLE_USERNAME")
    moodle_password: str = Field(..., alias="MOODLE_PASSWORD")
    moodle_headless: bool = Field(True, alias="MOODLE_HEADLESS")

    # --- LLM ---
    llm_provider: Literal["ollama", "openai", "groq", "anthropic"] = Field(..., alias="LLM_PROVIDER")
    llm_model: str = Field(..., alias="LLM_MODEL")

    llm_base_url: str | None = Field(None, alias="LLM_BASE_URL")
    llm_api_key: str | None = Field(None, alias="LLM_API_KEY")

    # --- App ---
    debug: bool = Field(False, alias="DEBUG")

    def to_moodle_settings(self) -> MoodleSettings:
        return MoodleSettings(
            base_url=self.moodle_base_url,
            username=self.moodle_username,
            password=self.moodle_password,
            headless=self.moodle_headless,
        )

    def to_llm_settings(self) -> LlmSettings:
        return LlmSettings(
            provider=self.llm_provider,
            model=self.llm_model,
            base_url=self.llm_base_url,
            api_key=self.llm_api_key,
        )


@lru_cache
def get_settings() -> AppSettings:
    """
    Cached settings instance.

    Ensures:
    - singleton behavior
    - no repeated .env parsing
    """
    return AppSettings()