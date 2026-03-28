from pydantic import BaseModel

from app.config import Settings as AppSettings
from app.config import get_settings as get_app_settings

class MoodleSettings(BaseModel):
    base_url: str
    username: str
    password: str
    headless: bool


class LlmSettings(BaseModel):
    provider: str
    model: str
    base_url: str | None = None
    api_key: str | None = None


def get_settings() -> AppSettings:
    """
    Compatibility wrapper around the unified application settings module.
    """
    return get_app_settings()
