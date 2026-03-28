from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.infrastructure.factories import build_app_container
from app.infrastructure.logging.setup import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifecycle manager.

    Responsibilities:
    - initialize logging
    - build application container
    - attach shared state to FastAPI app
    """

    settings = get_settings()

    # -----------------------------------------------------
    # Logging
    # -----------------------------------------------------
    setup_logging(debug=settings.debug)

    # -----------------------------------------------------
    # Dependency container
    # -----------------------------------------------------
    def rebuild_container():
        get_settings.cache_clear()
        refreshed_settings = get_settings()
        setup_logging(debug=refreshed_settings.debug)
        container = build_app_container(settings=refreshed_settings)
        app.state.container = container
        return container

    app.state.rebuild_container = rebuild_container
    app.state.container = build_app_container(settings=settings)

    # -----------------------------------------------------
    # Startup complete
    # -----------------------------------------------------
    yield

    # -----------------------------------------------------
    # Shutdown (future extension point)
    # -----------------------------------------------------
    # Aquí podrías:
    # - cerrar recursos
    # - limpiar caches
    # - detener servicios externos
