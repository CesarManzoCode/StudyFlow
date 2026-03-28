from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"
STATIC_DIR = APP_DIR / "static"
TEMPLATES_DIR = APP_DIR / "presentation" / "templates"


class LlmProvider(StrEnum):
    OPENAI = "openai"
    GROQ = "groq"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env files.

    The project is intentionally single-user and local-first, so settings are
    modeled as one coherent configuration object rather than fragmented modules.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Moodle AI Assistant"
    debug: bool = False

    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_access_key: SecretStr | None = None

    static_url_path: str = "/static"

    moodle_base_url: str = Field(..., description="Base URL of the Moodle instance.")
    moodle_username: str = Field(..., min_length=1)
    moodle_password: SecretStr = Field(...)

    llm_provider: LlmProvider = LlmProvider.OPENAI

    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-5.4-mini"

    groq_api_key: SecretStr | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    anthropic_api_key: SecretStr | None = None
    anthropic_model: str = "claude-sonnet-4-5"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:latest"

    @property
    def static_dir(self) -> Path:
        return STATIC_DIR

    @property
    def templates_dir(self) -> Path:
        return TEMPLATES_DIR

    @field_validator("moodle_base_url", mode="before")
    @classmethod
    def normalize_moodle_base_url(cls, value: str) -> str:
        normalized = value.strip()
        return normalized.rstrip("/")

    @field_validator("app_host")
    @classmethod
    def validate_app_host(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            msg = "APP_HOST must not be empty."
            raise ValueError(msg)
        return normalized

    @field_validator("static_url_path")
    @classmethod
    def validate_static_url_path(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized.startswith("/"):
            msg = "static_url_path must start with '/'."
            raise ValueError(msg)
        return normalized.rstrip("/") or "/static"

    @field_validator("ollama_base_url", mode="before")
    @classmethod
    def normalize_ollama_base_url(cls, value: str) -> str:
        normalized = value.strip()
        return normalized.rstrip("/")

    @field_validator("app_port")
    @classmethod
    def validate_app_port(cls, value: int) -> int:
        if not (1 <= value <= 65535):
            msg = "APP_PORT must be between 1 and 65535."
            raise ValueError(msg)
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the cached application settings.

    The settings object is cached because configuration is effectively static
    for the lifetime of the process in this project.
    """
    return Settings()