from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import get_settings


settings = get_settings()
templates = Jinja2Templates(directory=str(settings.templates_dir))

router = APIRouter(tags=["pages"])


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    """
    Render the main dashboard page.

    At this stage the page is intentionally static from the server perspective.
    Dynamic task synchronization and AI interactions will be added through
    dedicated application use cases and route modules later.
    """
    context = {
        "request": request,
        "page_title": "Dashboard",
        "app_name": settings.app_name,
        "moodle_base_url": settings.moodle_base_url,
        "moodle_username": settings.moodle_username,
        "llm_provider": settings.llm_provider.value,
        "llm_model": _resolve_active_model_name(),
    }
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context=context,
    )


def _resolve_active_model_name() -> str:
    """
    Resolve the configured model name for the currently selected LLM provider.
    """
    provider_to_model = {
        "openai": settings.openai_model,
        "groq": settings.groq_model,
        "anthropic": settings.anthropic_model,
        "ollama": settings.ollama_model,
    }
    return provider_to_model[settings.llm_provider.value]