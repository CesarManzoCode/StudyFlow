from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.application.use_cases.save_settings import SaveSettingsUseCase
from app.application.use_cases.validate_provider import ValidateProviderUseCase
from app.domain.exceptions import InvalidLlmResponseError
from app.infrastructure.config.settings import get_settings


router = APIRouter(prefix="/settings", tags=["settings"])

templates = Jinja2Templates(directory="app/presentation/templates")

settings = get_settings()

save_settings_uc = SaveSettingsUseCase()
validate_provider_uc = ValidateProviderUseCase()


@router.get("", response_class=HTMLResponse)
async def settings_page(request: Request):
    """
    Render settings page.
    """
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "page_title": "Settings",
            "settings": settings,
            "error": None,
        },
    )


@router.post("", response_class=HTMLResponse)
async def save_settings(
    request: Request,
    moodle_base_url: str = Form(...),
    moodle_username: str = Form(...),
    moodle_password: str = Form(...),
    llm_provider: str = Form(...),
    llm_model: str = Form(...),
    llm_api_key: str = Form(default=""),
    llm_base_url: str = Form(default=""),
):
    """
    Save settings and validate LLM provider.
    """
    try:
        # validar provider primero
        await validate_provider_uc.execute(
            provider=llm_provider,
            api_key=llm_api_key or None,
            base_url=llm_base_url or None,
        )

        # guardar configuración
        await save_settings_uc.execute(
            moodle_base_url=moodle_base_url,
            moodle_username=moodle_username,
            moodle_password=moodle_password,
            llm_provider=llm_provider,
            llm_model=llm_model,
            llm_api_key=llm_api_key or None,
            llm_base_url=llm_base_url or None,
        )

        return RedirectResponse("/settings", status_code=303)

    except InvalidLlmResponseError as exc:
        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "page_title": "Settings",
                "settings": settings,
                "error": str(exc),
            },
            status_code=400,
        )

    except Exception as exc:
        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "page_title": "Settings",
                "settings": settings,
                "error": f"Unexpected error: {exc!s}",
            },
            status_code=500,
        )