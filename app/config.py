from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"
STATIC_DIR = APP_DIR / "static"
TEMPLATES_DIR = APP_DIR / "presentation" / "templates"


class Settings(BaseSettings):
    """
    Unified application settings.

    The project persists configuration in a local `.env` file, but the app
    also ships with safe demo defaults so it can boot cleanly on a fresh clone
    before the user configures real Moodle or LLM credentials.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "StudyFlow"
    debug: bool = False

    app_host: str = "127.0.0.1"
    app_port: int = 8000
    static_url_path: str = "/static"

    moodle_base_url: str = "https://example.edu/moodle"
    moodle_username: str = "demo.student"
    moodle_password: str = "demo-password"
    moodle_headless: bool = True

    llm_provider: Literal["ollama", "openai", "groq", "anthropic"] = "ollama"
    llm_model: str = "demo-checklist"
    llm_language: str = "Spanish"
    llm_base_url: str | None = "http://localhost:11434"
    llm_api_key: str | None = None

    @property
    def static_dir(self) -> Path:
        return STATIC_DIR

    @property
    def templates_dir(self) -> Path:
        return TEMPLATES_DIR

    @field_validator("moodle_base_url", mode="before")
    @classmethod
    def normalize_moodle_base_url(cls, value: str) -> str:
        normalized = str(value).strip()
        return normalized.rstrip("/")

    @field_validator(
        "moodle_username",
        "moodle_password",
        "llm_model",
        "llm_language",
        mode="before",
    )
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        normalized = str(value).strip()
        if not normalized:
            msg = "Configuration values must not be empty."
            raise ValueError(msg)
        return normalized

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

    @field_validator("llm_base_url", mode="before")
    @classmethod
    def normalize_llm_base_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            return None
        return normalized.rstrip("/")

    @field_validator("llm_api_key", mode="before")
    @classmethod
    def normalize_optional_secret(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("debug", "moodle_headless", mode="before")
    @classmethod
    def normalize_bool_like_values(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            normalized = value.strip().casefold()
            if normalized in {"1", "true", "yes", "on", "debug", "development"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "production"}:
                return False

        return bool(value)

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
