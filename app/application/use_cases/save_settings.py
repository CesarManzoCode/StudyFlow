from __future__ import annotations

from pathlib import Path

from app.config import BASE_DIR, get_settings


class SaveSettingsUseCase:
    """
    Persist local application settings into the project's `.env` file.
    """

    def __init__(self, env_path: Path | None = None) -> None:
        self._env_path = env_path or BASE_DIR / ".env"

    async def execute(
        self,
        *,
        moodle_base_url: str,
        moodle_username: str,
        moodle_password: str,
        llm_provider: str,
        llm_model: str,
        llm_language: str,
        llm_api_key: str | None = None,
        llm_base_url: str | None = None,
    ) -> None:
        current_settings = get_settings()

        content = self._render_env_file(
            moodle_base_url=moodle_base_url.strip(),
            moodle_username=moodle_username.strip(),
            moodle_password=moodle_password.strip(),
            moodle_headless=current_settings.moodle_headless,
            llm_provider=llm_provider.strip(),
            llm_model=llm_model.strip(),
            llm_language=llm_language.strip(),
            llm_api_key=(llm_api_key or "").strip(),
            llm_base_url=(llm_base_url or "").strip(),
            debug=current_settings.debug,
            app_host=current_settings.app_host,
            app_port=current_settings.app_port,
        )

        self._env_path.write_text(content, encoding="utf-8")
        get_settings.cache_clear()

    def _render_env_file(
        self,
        *,
        moodle_base_url: str,
        moodle_username: str,
        moodle_password: str,
        moodle_headless: bool,
        llm_provider: str,
        llm_model: str,
        llm_language: str,
        llm_api_key: str,
        llm_base_url: str,
        debug: bool,
        app_host: str,
        app_port: int,
    ) -> str:
        lines = [
            "# --- App ---",
            f"APP_HOST={self._serialize_env_value(app_host)}",
            f"APP_PORT={app_port}",
            f"DEBUG={'true' if debug else 'false'}",
            "",
            "# --- Moodle ---",
            f"MOODLE_BASE_URL={self._serialize_env_value(moodle_base_url)}",
            f"MOODLE_USERNAME={self._serialize_env_value(moodle_username)}",
            f"MOODLE_PASSWORD={self._serialize_env_value(moodle_password)}",
            f"MOODLE_HEADLESS={'true' if moodle_headless else 'false'}",
            "",
            "# --- LLM ---",
            f"LLM_PROVIDER={self._serialize_env_value(llm_provider)}",
            f"LLM_MODEL={self._serialize_env_value(llm_model)}",
            f"LLM_LANGUAGE={self._serialize_env_value(llm_language)}",
            f"LLM_BASE_URL={self._serialize_env_value(llm_base_url)}",
            f"LLM_API_KEY={self._serialize_env_value(llm_api_key)}",
            "",
        ]
        return "\n".join(lines)

    def _serialize_env_value(self, value: str) -> str:
        if value == "":
            return '""'

        if any(character in value for character in (' ', '#', '"')):
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'

        return value
