from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import get_settings


router = APIRouter(tags=["health"])


@router.get("/health", response_class=JSONResponse)
async def healthcheck() -> JSONResponse:
    """
    Lightweight health endpoint for local runtime verification.

    This endpoint intentionally verifies only that the web application is
    running and that core configuration was loaded successfully. It does not
    attempt network calls, scraping, or LLM provider checks.
    """
    settings = get_settings()

    payload = {
        "status": "ok",
        "app_name": settings.app_name,
        "debug": settings.debug,
    }
    return JSONResponse(content=payload)