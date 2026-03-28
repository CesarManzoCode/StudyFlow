from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.domain.exceptions import InvalidLlmResponseError, LlmProviderError, TaskNotFoundError
from app.infrastructure.factories import AppContainer
from app.presentation.forms.ai_help_form import AiHelpForm
from app.presentation.viewmodels.tasks import map_task_to_viewmodel


router = APIRouter(prefix="/tasks", tags=["tasks"])
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory=str(get_settings().templates_dir))
templates.env.globals["app_name"] = get_settings().app_name


def _get_container(request: Request) -> AppContainer:
    return request.app.state.container


async def _build_task_context(
    request: Request,
    task_id: str,
    *,
    checklist=None,
    ai_form: AiHelpForm | None = None,
    success: str | None = None,
    error: str | None = None,
) -> dict[str, object]:
    container = _get_container(request)
    task = await container.get_task_detail.execute(task_id)
    task_view_model = map_task_to_viewmodel(task)

    return {
        "request": request,
        "page_title": task_view_model.title,
        "task": task_view_model,
        "checklist": checklist,
        "ai_form": ai_form or AiHelpForm(),
        "success": success,
        "error": error,
        "info": None,
    }


def _not_found_context(request: Request, *, error: str | None = None) -> dict[str, object]:
    return {
        "request": request,
        "page_title": "Task not found",
        "task": None,
        "checklist": None,
        "ai_form": AiHelpForm(),
        "success": None,
        "error": error or "The requested task is not available in the current snapshot.",
        "info": None,
    }


@router.get("/{task_id}", response_class=HTMLResponse)
async def task_detail(request: Request, task_id: str):
    """
    Render task detail page.
    """
    try:
        context = await _build_task_context(request, task_id)
        return templates.TemplateResponse(request, "task_detail.html", context)
    except TaskNotFoundError:
        return templates.TemplateResponse(
            request,
            "task_detail.html",
            _not_found_context(request),
            status_code=404,
        )


@router.post("/{task_id}/help", response_class=HTMLResponse)
async def generate_task_help(
    request: Request,
    task_id: str,
    form: AiHelpForm = Depends(AiHelpForm.from_form),
):
    """
    Generate AI checklist for a task.
    """
    container = _get_container(request)

    try:
        checklist = await container.generate_task_help.execute(
            task_id=task_id,
            user_question=form.user_question,
        )
        context = await _build_task_context(
            request,
            task_id,
            checklist=checklist,
            ai_form=form,
            success="AI checklist generated successfully.",
        )
        return templates.TemplateResponse(request, "task_detail.html", context)
    except TaskNotFoundError:
        return templates.TemplateResponse(
            request,
            "task_detail.html",
            _not_found_context(request),
            status_code=404,
        )
    except (InvalidLlmResponseError, LlmProviderError) as exc:
        context = await _build_task_context(
            request,
            task_id,
            ai_form=form,
            error=f"Could not generate AI help: {exc!s}",
        )
        return templates.TemplateResponse(request, "task_detail.html", context, status_code=502)
    except Exception as exc:
        logger.exception("Unexpected AI help error", exc_info=exc)
        context = await _build_task_context(
            request,
            task_id,
            ai_form=form,
            error="Unexpected AI help error. Please retry in a moment.",
        )
        return templates.TemplateResponse(request, "task_detail.html", context, status_code=500)
