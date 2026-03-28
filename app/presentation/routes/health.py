from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse


router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check() -> JSONResponse:
    """
    Basic health check endpoint.

    Returns:
        JSON response indicating service status.
    """
    return JSONResponse(
        {
            "status": "ok",
        }
    )