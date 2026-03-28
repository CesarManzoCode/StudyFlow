from datetime import datetime
from types import SimpleNamespace

import pytest

from app.config import Settings
from app.domain.enums import TaskStatus
from app.domain.models.task import Task
from app.infrastructure import factories


def _settings(**overrides: object) -> Settings:
    base = {
        "moodle_base_url": "https://example.edu/moodle",
        "moodle_username": "demo.student",
        "moodle_password": "secret",
        "moodle_headless": True,
        "llm_provider": "ollama",
        "llm_model": "demo-checklist",
        "llm_language": "Spanish",
        "llm_base_url": "http://localhost:11434",
        "llm_api_key": None,
    }
    base.update(overrides)
    return Settings(**base)


def test_should_use_demo_moodle_rules() -> None:
    assert factories._should_use_demo_moodle(_settings(moodle_base_url="https://example.edu/moodle"))
    assert factories._should_use_demo_moodle(_settings(moodle_username="demo.anyone"))
    assert not factories._should_use_demo_moodle(
        _settings(
            moodle_base_url="https://campus.real-university.edu/moodle",
            moodle_username="student01",
        )
    )


def test_build_moodle_client_returns_demo_client_for_demo_settings() -> None:
    client = factories._build_moodle_client(_settings())
    assert client.__class__.__name__ == "_DemoMoodleClient"


def test_build_llm_client_returns_demo_for_demo_model() -> None:
    client = factories._build_llm_client(_settings(llm_model="demo-checklist"))
    assert client.__class__.__name__ == "_DemoLlmClient"


def test_build_llm_client_returns_demo_when_openai_key_missing() -> None:
    client = factories._build_llm_client(
        _settings(llm_provider="openai", llm_model="gpt-5.4-nano", llm_api_key=None)
    )
    assert client.__class__.__name__ == "_DemoLlmClient"


def test_build_llm_client_unsupported_provider_falls_back_to_demo() -> None:
    settings = SimpleNamespace(
        llm_provider="unsupported",
        llm_model="x",
        llm_base_url=None,
        llm_api_key=None,
    )

    client = factories._build_llm_client(settings)
    assert client.__class__.__name__ == "_DemoLlmClient"


@pytest.mark.asyncio
async def test_demo_moodle_client_fetch_tasks_and_fetch_detail() -> None:
    client = factories._DemoMoodleClient(base_url="https://example.edu/moodle")

    tasks = await client.fetch_tasks()
    assert len(tasks) == 3

    detail = await client.fetch_task_detail(tasks[0].url)
    assert "StudyFlow demo mode" in (detail.description_text or "")

    fallback = await client.fetch_task_detail("https://example.edu/moodle/unknown")
    assert fallback.id == "demo-task"


@pytest.mark.asyncio
async def test_demo_llm_client_generate_checklist_handles_custom_request() -> None:
    task = Task(
        id="task-1",
        course_name="Chemistry",
        title="Report",
        due_at=datetime(2026, 4, 1, 18, 0),
        status=TaskStatus.PENDING,
        url="https://example.edu/task-1",
    )
    client = factories._DemoLlmClient(provider="ollama", model="demo-checklist")

    checklist = await client.generate_checklist(
        task=task,
        user_question="Student request:\nPlease focus on rubric alignment.",
    )

    assert checklist.summary
    assert checklist.deliverable
    assert any("student's latest request" in step for step in checklist.steps)


def test_build_app_container_returns_wired_container() -> None:
    container = factories.build_app_container(_settings())

    assert container.settings.app_name == "StudyFlow"
    assert container.task_repository is not None
    assert container.list_tasks is not None
    assert container.generate_task_help is not None
