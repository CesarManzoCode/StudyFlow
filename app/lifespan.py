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
    container = build_app_container()

    # attach to app state (single source of truth)
    app.state.container = container

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