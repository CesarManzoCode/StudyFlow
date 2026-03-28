from fastapi import APIRouter

from app.presentation.routes.pages import router as pages_router


router = APIRouter()
router.include_router(pages_router)