from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.presentation.routes import router as app_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """
    Application lifecycle manager.

    This project currently does not require long-lived external resources during
    startup or shutdown, but defining the lifespan explicitly establishes a
    stable extension point for future initialization tasks such as:

    - warming in-memory caches
    - validating critical configuration
    - preparing Playwright runtime dependencies
    - initializing structured logging sinks
    """
    yield


def create_app() -> FastAPI:
    """
    Application factory.

    Returns:
        A fully configured FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.mount(
        settings.static_url_path,
        StaticFiles(directory=settings.static_dir),
        name="static",
    )

    app.include_router(app_router)

    return app


app = create_app()