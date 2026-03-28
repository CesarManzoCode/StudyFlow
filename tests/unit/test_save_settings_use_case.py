from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.application.use_cases import save_settings as save_settings_module
from app.application.use_cases.save_settings import SaveSettingsUseCase


@pytest.mark.asyncio
async def test_execute_writes_expected_env_file_and_clears_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_path = tmp_path / ".env"
    use_case = SaveSettingsUseCase(env_path=env_path)

    fake_cache_clear = Mock()

    def fake_get_settings() -> SimpleNamespace:
        return SimpleNamespace(
            moodle_headless=True,
            debug=False,
            app_host="127.0.0.1",
            app_port=8000,
        )

    fake_get_settings.cache_clear = fake_cache_clear  # type: ignore[attr-defined]

    monkeypatch.setattr(save_settings_module, "get_settings", fake_get_settings)

    await use_case.execute(
        moodle_base_url=" https://example.edu/moodle ",
        moodle_username=" student ",
        moodle_password=" pass with spaces ",
        llm_provider=" openai ",
        llm_model=" gpt-5.4-nano ",
        llm_language=" Spanish ",
        llm_api_key=" key#123 ",
        llm_base_url=" https://api.example.com/v1 ",
    )

    content = env_path.read_text(encoding="utf-8")

    assert "APP_HOST=127.0.0.1" in content
    assert "APP_PORT=8000" in content
    assert "DEBUG=false" in content
    assert "MOODLE_BASE_URL=https://example.edu/moodle" in content
    assert "MOODLE_USERNAME=student" in content
    assert 'MOODLE_PASSWORD="pass with spaces"' in content
    assert "MOODLE_HEADLESS=true" in content
    assert "LLM_PROVIDER=openai" in content
    assert "LLM_MODEL=gpt-5.4-nano" in content
    assert "LLM_LANGUAGE=Spanish" in content
    assert "LLM_BASE_URL=https://api.example.com/v1" in content
    assert 'LLM_API_KEY="key#123"' in content

    fake_cache_clear.assert_called_once()


def test_serialize_env_value_quotes_when_needed() -> None:
    use_case = SaveSettingsUseCase(env_path=Path("/tmp/does-not-matter"))

    assert use_case._serialize_env_value("") == '""'
    assert use_case._serialize_env_value("plain") == "plain"
    assert use_case._serialize_env_value("has space") == '"has space"'
    assert use_case._serialize_env_value("has#hash") == '"has#hash"'
    assert use_case._serialize_env_value('has"quote') == '"has\\"quote"'
