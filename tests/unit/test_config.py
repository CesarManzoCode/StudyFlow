import pytest

from app import config as config_module
from app.config import Settings


def test_settings_normalize_values_and_bool_like_inputs() -> None:
    settings = Settings(
        moodle_base_url=" https://example.edu/moodle/ ",
        moodle_username=" student ",
        moodle_password=" secret ",
        llm_model=" qwen3:latest ",
        app_host=" 127.0.0.1 ",
        static_url_path="/assets/",
        llm_base_url=" http://localhost:11434/ ",
        llm_api_key=" key ",
        debug="development",
        moodle_headless="off",
    )

    assert settings.moodle_base_url == "https://example.edu/moodle"
    assert settings.moodle_username == "student"
    assert settings.moodle_password == "secret"
    assert settings.llm_model == "qwen3:latest"
    assert settings.app_host == "127.0.0.1"
    assert settings.static_url_path == "/assets"
    assert settings.llm_base_url == "http://localhost:11434"
    assert settings.llm_api_key == "key"
    assert settings.debug is True
    assert settings.moodle_headless is False


def test_settings_rejects_invalid_port() -> None:
    with pytest.raises(ValueError, match="APP_PORT must be between 1 and 65535"):
        Settings(
            app_port=70000,
            moodle_base_url="https://example.edu/moodle",
            moodle_username="student",
            moodle_password="secret",
            llm_model="qwen3:latest",
        )


def test_settings_rejects_invalid_static_url_path() -> None:
    with pytest.raises(ValueError, match="static_url_path must start with '/'"):
        Settings(
            static_url_path="assets",
            moodle_base_url="https://example.edu/moodle",
            moodle_username="student",
            moodle_password="secret",
            llm_model="qwen3:latest",
        )


def test_get_settings_is_cached() -> None:
    config_module.get_settings.cache_clear()

    first = config_module.get_settings()
    second = config_module.get_settings()

    assert first is second
