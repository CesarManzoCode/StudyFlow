from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.lifespan import lifespan
from app.presentation.routes import router as app_router


def create_app() -> FastAPI:
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