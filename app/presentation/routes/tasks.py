from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.domain.exceptions import TaskNotFoundError
from app.infrastructure.factories import build_app_container


router = APIRouter(prefix="/tasks", tags=["tasks"])

templates = Jinja2Templates(directory="app/presentation/templates")

# ⚠️ IMPORTANTE: no recrear múltiples veces en producción real,
# pero para este proyecto local es aceptable.
container = build_app_container()


@router.get("/{task_id}", response_class=HTMLResponse)
async def task_detail(request: Request, task_id: str):
    """
    Render task detail page.
    """
    try:
        task = await container.get_task_detail.execute(task_id)

        return templates.TemplateResponse(
            "task_detail.html",
            {
                "request": request,
                "page_title": task.title,
                "task": task,
                "checklist": None,
            },
        )

    except TaskNotFoundError:
        return templates.TemplateResponse(
            "task_detail.html",
            {
                "request": request,
                "page_title": "Task not found",
                "task": None,
                "checklist": None,
            },
            status_code=404,
        )


@router.post("/{task_id}/help", response_class=HTMLResponse)
async def generate_task_help(
    request: Request,
    task_id: str,
    user_question: str = Form(default=""),
):
    """
    Generate AI checklist for a task.
    """
    try:
        checklist = await container.generate_task_help.execute(
            task_id=task_id,
            user_question=user_question or None,
        )

        task = await container.get_task_detail.execute(task_id)

        return templates.TemplateResponse(
            "task_detail.html",
            {
                "request": request,
                "page_title": task.title,
                "task": task,
                "checklist": checklist,
            },
        )

    except TaskNotFoundError:
        return templates.TemplateResponse(
            "task_detail.html",
            {
                "request": request,
                "page_title": "Task not found",
                "task": None,
                "checklist": None,
            },
            status_code=404,
        )