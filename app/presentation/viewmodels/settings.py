from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SettingsViewModel:
    """
    UI-ready representation of application settings.
    """

    moodle_base_url: str
    moodle_username: str
    moodle_password: str
    moodle_headless: bool

    llm_provider: str
    llm_model: str
    llm_api_key: str
    llm_base_url: str


# =========================================================
# MAPPER
# =========================================================

def map_settings_to_viewmodel(
    *,
    moodle_base_url: str,
    moodle_username: str,
    moodle_password: str,
    moodle_headless: bool,
    llm_provider: str,
    llm_model: str,
    llm_api_key: str | None = None,
    llm_base_url: str | None = None,
) -> SettingsViewModel:
    """
    Normalize raw settings into a UI-safe structure.
    """
    return SettingsViewModel(
        moodle_base_url=moodle_base_url,
        moodle_username=moodle_username,
        moodle_password=moodle_password,
        moodle_headless=moodle_headless,
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_api_key=llm_api_key or "",
        llm_base_url=llm_base_url or "",
    )
