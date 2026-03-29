from fastapi import APIRouter

from app.presentation.routes.ai_help import router as ai_help_router
from app.presentation.routes.health import router as health_router
from app.presentation.routes.pages import router as pages_router
from app.presentation.routes.planning import router as planning_router
from app.presentation.routes.settings import router as settings_router
from app.presentation.routes.task_state import router as task_state_router
from app.presentation.routes.tasks import router as tasks_router


router = APIRouter()
router.include_router(pages_router)
router.include_router(tasks_router)
router.include_router(ai_help_router)
router.include_router(task_state_router)
router.include_router(planning_router)
router.include_router(settings_router)
router.include_router(health_router)
