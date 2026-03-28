from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient

from app.config import get_settings
from app.domain.enums import TaskPriority, TaskStatus
from app.domain.exceptions import InvalidLlmResponseError, TaskNotFoundError
from app.domain.models.checklist import ChecklistResponse
from app.domain.models.task import Task
from app.presentation.routes import router as app_router


def _task(task_id: str = "task-1") -> Task:
    return Task(
        id=task_id,
        course_name="Software Engineering",
        title="Sprint retrospective",
        description_text="Write retrospective notes.",
        due_at=datetime(2026, 4, 2, 20, 0),
        status=TaskStatus.PENDING,
        url=f"https://example.edu/{task_id}",
    )


def _container() -> SimpleNamespace:
    task = _task()
    settings = SimpleNamespace(
        moodle_base_url="https://example.edu/moodle",
        moodle_username="demo.student",
        moodle_password="stored-password",
        moodle_headless=True,
        llm_provider="ollama",
        llm_model="demo-checklist",
        llm_language="Spanish",
        llm_api_key="stored-api-key",
        llm_base_url="http://localhost:11434",
    )

    task_repository = SimpleNamespace(last_synced_at=AsyncMock(return_value=datetime(2026, 3, 28, 12, 0)))

    return SimpleNamespace(
        settings=settings,
        task_repository=task_repository,
        list_tasks=SimpleNamespace(
            execute=AsyncMock(return_value=[task.with_priority(TaskPriority.HIGH)])
        ),
        sync_tasks=SimpleNamespace(execute=AsyncMock(return_value=[task])),
        get_task_detail=SimpleNamespace(execute=AsyncMock(return_value=task)),
        generate_task_help=SimpleNamespace(
            execute=AsyncMock(
                return_value=ChecklistResponse(
                    summary="Summary",
                    deliverable="Deliverable",
                    steps=["Step 1"],
                    warnings=[],
                    questions_to_clarify=[],
                    final_checklist=["Done"],
                )
            )
        ),
        validate_provider=SimpleNamespace(execute=AsyncMock(return_value=None)),
        save_settings=SimpleNamespace(execute=AsyncMock(return_value=None)),
    )


def _client() -> TestClient:
    settings = get_settings()
    app = FastAPI()
    app.mount(
        settings.static_url_path,
        StaticFiles(directory=settings.static_dir),
        name="static",
    )
    app.include_router(app_router)
    return TestClient(app)


def test_health_returns_ok() -> None:
    container = _container()
    with _client() as client:
        client.app.state.container = container
        client.app.state.rebuild_container = Mock(return_value=container)
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_dashboard_renders_tasks() -> None:
    container = _container()
    with _client() as client:
        client.app.state.container = container
        client.app.state.rebuild_container = Mock(return_value=container)
        response = client.get("/")

    assert response.status_code == 200
    assert "Sprint retrospective" in response.text


def test_sync_redirects_on_success() -> None:
    container = _container()
    with _client() as client:
        client.app.state.container = container
        client.app.state.rebuild_container = Mock(return_value=container)
        response = client.post("/sync", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/?sync=ok"


def test_sync_returns_502_on_failure() -> None:
    container = _container()
    container.sync_tasks.execute = AsyncMock(side_effect=RuntimeError("sync failed"))

    with _client() as client:
        client.app.state.container = container
        client.app.state.rebuild_container = Mock(return_value=container)
        response = client.post("/sync")

    assert response.status_code == 502
    assert "Task synchronization failed" in response.text


def test_task_detail_success_and_not_found() -> None:
    container = _container()

    with _client() as client:
        client.app.state.container = container
        client.app.state.rebuild_container = Mock(return_value=container)
        ok_response = client.get("/tasks/task-1")
        assert ok_response.status_code == 200
        assert "Sprint retrospective" in ok_response.text

        container.get_task_detail.execute = AsyncMock(side_effect=TaskNotFoundError("missing"))
        not_found_response = client.get("/tasks/missing")

    assert not_found_response.status_code == 404
    assert "Task not found" in not_found_response.text


def test_generate_task_help_success_and_error_paths() -> None:
    container = _container()

    with _client() as client:
        client.app.state.container = container
        client.app.state.rebuild_container = Mock(return_value=container)
        ok_response = client.post("/tasks/task-1/help", data={"user_question": "Focus steps"})
        assert ok_response.status_code == 200
        assert "AI checklist generated successfully" in ok_response.text

        container.generate_task_help.execute = AsyncMock(
            side_effect=InvalidLlmResponseError("bad response")
        )
        provider_error_response = client.post("/tasks/task-1/help", data={"user_question": "x"})

        container.generate_task_help.execute = AsyncMock(side_effect=RuntimeError("boom"))
        unexpected_error_response = client.post("/tasks/task-1/help", data={"user_question": "x"})

    assert provider_error_response.status_code == 502
    assert "Could not generate AI help" in provider_error_response.text
    assert unexpected_error_response.status_code == 500
    assert "Unexpected AI help error" in unexpected_error_response.text


def test_settings_get_and_save_preserve_secret_values_when_blank() -> None:
    container = _container()

    with _client() as client:
        client.app.state.container = container
        client.app.state.rebuild_container = Mock(return_value=container)
        get_response = client.get("/settings")
        assert get_response.status_code == 200

        post_response = client.post(
            "/settings",
            data={
                "moodle_base_url": "https://example.edu/moodle",
                "moodle_username": "demo.student",
                "moodle_password": "",
                "llm_provider": "openai",
                "llm_model": "gpt-5.4-nano",
                "llm_language": "Spanish",
                "llm_api_key": "",
                "llm_base_url": "https://api.openai.com/v1",
            },
            follow_redirects=False,
        )

    assert post_response.status_code == 303
    assert post_response.headers["location"] == "/settings?saved=1"

    kwargs = container.save_settings.execute.await_args.kwargs
    assert kwargs["moodle_password"] == "stored-password"
    assert kwargs["llm_api_key"] == "stored-api-key"
    assert kwargs["llm_language"] == "Spanish"


def test_settings_save_returns_400_on_validation_error() -> None:
    container = _container()
    container.validate_provider.execute = AsyncMock(side_effect=InvalidLlmResponseError("Invalid"))

    with _client() as client:
        client.app.state.container = container
        client.app.state.rebuild_container = Mock(return_value=container)
        response = client.post(
            "/settings",
            data={
                "moodle_base_url": "https://example.edu/moodle",
                "moodle_username": "demo.student",
                "moodle_password": "",
                "llm_provider": "openai",
                "llm_model": "gpt-5.4-nano",
                "llm_language": "Spanish",
                "llm_api_key": "",
                "llm_base_url": "https://api.openai.com/v1",
            },
        )

    assert response.status_code == 400
    assert "Invalid" in response.text


def test_settings_saved_message_is_rendered_from_query_flag() -> None:
    container = _container()
    with _client() as client:
        client.app.state.container = container
        client.app.state.rebuild_container = Mock(return_value=container)
        response = client.get("/settings?saved=1")

    assert response.status_code == 200
    assert "Settings saved and container reloaded" in response.text


def test_settings_template_does_not_prefill_secret_inputs() -> None:
    container = _container()
    with _client() as client:
        client.app.state.container = container
        client.app.state.rebuild_container = Mock(return_value=container)
        response = client.get("/settings")

    assert response.status_code == 200
    assert 'name="moodle_password"' in response.text
    assert 'name="llm_api_key"' in response.text
    assert "stored-password" not in response.text
    assert "stored-api-key" not in response.text


def test_route_templates_use_app_name_global() -> None:
    container = _container()
    expected_app_name = get_settings().app_name

    with _client() as client:
        client.app.state.container = container
        client.app.state.rebuild_container = Mock(return_value=container)
        dashboard = client.get("/")
        settings = client.get("/settings")

    assert expected_app_name in dashboard.text
    assert expected_app_name in settings.text
