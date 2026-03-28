from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.infrastructure.factories import AppContainer
from app.presentation.viewmodels.settings import map_settings_to_viewmodel
from app.presentation.viewmodels.tasks import map_task_list


router = APIRouter(tags=["pages"])
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory=str(get_settings().templates_dir))
templates.env.globals["app_name"] = get_settings().app_name


def _get_container(request: Request) -> AppContainer:
    return request.app.state.container


async def _build_dashboard_context(
    request: Request,
    *,
    success: str | None = None,
    error: str | None = None,
) -> dict[str, object]:
    container = _get_container(request)
    tasks = []
    last_sync = None

    try:
        prioritized_tasks = await container.list_tasks.execute(now=datetime.now())
        tasks = map_task_list(prioritized_tasks)
        last_sync = await container.task_repository.last_synced_at()
    except Exception as exc:
        logger.exception("Could not load tasks for dashboard", exc_info=exc)
        if error is None:
            error = "Could not load tasks. Please try syncing again."

    settings_vm = map_settings_to_viewmodel(
        moodle_base_url=container.settings.moodle_base_url,
        moodle_username=container.settings.moodle_username,
        moodle_headless=container.settings.moodle_headless,
        llm_provider=container.settings.llm_provider,
        llm_model=container.settings.llm_model,
        llm_language=container.settings.llm_language,
        llm_base_url=container.settings.llm_base_url,
    )

    if success is None and request.query_params.get("sync") == "ok":
        success = "Tasks synchronized successfully."

    return {
        "request": request,
        "page_title": "Dashboard",
        "tasks": tasks,
        "settings": settings_vm,
        "last_sync": last_sync,
        "last_sync_display": last_sync.strftime("%Y-%m-%d %H:%M") if last_sync else None,
        "success": success,
        "error": error,
        "info": None,
    }


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Render main dashboard.
    """
    context = await _build_dashboard_context(request)
    return templates.TemplateResponse(request, "dashboard.html", context)


@router.post("/sync", response_class=HTMLResponse)
async def sync_tasks(request: Request):
    """
    Synchronize tasks and return to the dashboard.
    """
    container = _get_container(request)

    try:
        await container.sync_tasks.execute(synced_at=datetime.now())
    except Exception as exc:
        logger.exception("Task synchronization failed", exc_info=exc)
        context = await _build_dashboard_context(
            request,
            error="Task synchronization failed. Check your Moodle settings and try again.",
        )
        return templates.TemplateResponse(request, "dashboard.html", context, status_code=502)

    return RedirectResponse(url="/?sync=ok", status_code=303)
