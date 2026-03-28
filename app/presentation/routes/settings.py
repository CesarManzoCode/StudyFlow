from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.domain.exceptions import InvalidLlmResponseError
from app.infrastructure.factories import AppContainer
from app.presentation.forms.settings_form import SettingsForm
from app.presentation.viewmodels.settings import map_settings_to_viewmodel


router = APIRouter(prefix="/settings", tags=["settings"])
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory=str(get_settings().templates_dir))
templates.env.globals["app_name"] = get_settings().app_name


def _get_container(request: Request) -> AppContainer:
    return request.app.state.container


def _map_container_settings(container: AppContainer):
    return map_settings_to_viewmodel(
        moodle_base_url=container.settings.moodle_base_url,
        moodle_username=container.settings.moodle_username,
        moodle_headless=container.settings.moodle_headless,
        llm_provider=container.settings.llm_provider,
        llm_model=container.settings.llm_model,
        llm_base_url=container.settings.llm_base_url,
    )


def _map_form_settings(form: SettingsForm):
    return map_settings_to_viewmodel(
        moodle_base_url=form.moodle_base_url,
        moodle_username=form.moodle_username,
        moodle_headless=True,
        llm_provider=form.llm_provider,
        llm_model=form.llm_model,
        llm_base_url=form.llm_base_url,
    )


@router.get("", response_class=HTMLResponse)
async def settings_page(request: Request):
    """
    Render settings page.
    """
    container = _get_container(request)
    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "request": request,
            "page_title": "Settings",
            "settings": _map_container_settings(container),
            "success": (
                "Settings saved and container reloaded."
                if request.query_params.get("saved") == "1"
                else None
            ),
            "error": None,
            "info": None,
        },
    )


@router.post("", response_class=HTMLResponse)
async def save_settings(
    request: Request,
    form: SettingsForm = Depends(SettingsForm.from_form),
):
    """
    Save settings and validate LLM provider.
    """
    container = _get_container(request)

    try:
        resolved_moodle_password = form.moodle_password or container.settings.moodle_password
        resolved_llm_api_key = form.llm_api_key or container.settings.llm_api_key

        await container.validate_provider.execute(
            provider=form.llm_provider,
            model=form.llm_model,
            api_key=resolved_llm_api_key,
            base_url=form.llm_base_url,
        )

        await container.save_settings.execute(
            moodle_base_url=form.moodle_base_url,
            moodle_username=form.moodle_username,
            moodle_password=resolved_moodle_password,
            llm_provider=form.llm_provider,
            llm_model=form.llm_model,
            llm_api_key=resolved_llm_api_key,
            llm_base_url=form.llm_base_url,
        )
        request.app.state.rebuild_container()

        return RedirectResponse("/settings?saved=1", status_code=303)

    except InvalidLlmResponseError as exc:
        return templates.TemplateResponse(
            request,
            "settings.html",
            {
                "request": request,
                "page_title": "Settings",
                "settings": _map_form_settings(form),
                "success": None,
                "error": str(exc),
                "info": None,
            },
            status_code=400,
        )

    except Exception as exc:
        logger.exception("Unexpected error while saving settings", exc_info=exc)
        return templates.TemplateResponse(
            request,
            "settings.html",
            {
                "request": request,
                "page_title": "Settings",
                "settings": _map_form_settings(form),
                "success": None,
                "error": "Unexpected error while saving settings.",
                "info": None,
            },
            status_code=500,
        )
