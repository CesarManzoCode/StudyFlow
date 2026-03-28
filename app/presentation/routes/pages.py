from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.infrastructure.factories import build_app_container


router = APIRouter(tags=["pages"])

templates = Jinja2Templates(directory="app/presentation/templates")

container = build_app_container()


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Render main dashboard.
    """
    tasks = []
    last_sync = None

    try:
        tasks = await container.list_tasks.execute(now=datetime.now())
        last_sync = await container.task_repository.last_synced_at()
    except Exception:
        # Dashboard must never crash
        # Fail silently and show empty state
        pass

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "page_title": "Dashboard",
            "tasks": tasks,
            "last_sync": last_sync,

            # config display (already used in template)
            "moodle_base_url": container.moodle_client._base_url,
            "moodle_username": container.moodle_client._username,
            "llm_provider": container.llm_client.__class__.__name__,
            "llm_model": getattr(container.llm_client, "_model", "unknown"),
        },
    )