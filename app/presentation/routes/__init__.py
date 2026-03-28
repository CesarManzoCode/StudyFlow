from fastapi import APIRouter

from app.presentation.routes.health import router as health_router
from app.presentation.routes.pages import router as pages_router
from app.presentation.routes.settings import router as settings_router
from app.presentation.routes.tasks import router as tasks_router


router = APIRouter()
router.include_router(pages_router)
router.include_router(tasks_router)
router.include_router(settings_router)
router.include_router(health_router)
