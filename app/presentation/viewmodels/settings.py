from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SettingsViewModel:
    """
    UI-ready representation of application settings.
    """

    moodle_base_url: str
    moodle_username: str

    llm_provider: str
    llm_model: str


# =========================================================
# MAPPER
# =========================================================

def map_settings_to_viewmodel(
    *,
    moodle_base_url: str,
    moodle_username: str,
    llm_provider: str,
    llm_model: str,
) -> SettingsViewModel:
    """
    Normalize raw settings into a UI-safe structure.
    """
    return SettingsViewModel(
        moodle_base_url=moodle_base_url,
        moodle_username=moodle_username,
        llm_provider=llm_provider,
        llm_model=llm_model,
    )