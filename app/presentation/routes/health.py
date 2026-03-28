from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse


router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check(request: Request) -> JSONResponse:
    """
    Basic health check endpoint.

    Returns:
        JSON response indicating service status.
    """
    _ = request
    return JSONResponse(
        {
            "status": "ok",
        }
    )
