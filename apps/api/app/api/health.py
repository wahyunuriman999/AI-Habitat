"""API v1 health and version endpoints.

/health  — application-level health (DB connectivity, environment info).
/version — application name, version, and environment.

These are mounted under /api/v1 by the API router.
The root /health (infrastructure/liveness) is defined in main.py.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import settings
from app.core.database import get_engine
from app.core.response import success_response

router = APIRouter()


@router.get("/health")
async def api_health(db_engine: AsyncEngine = Depends(get_engine)):
    """Application/API health check.

    Runs ``SELECT 1`` against the database to verify real connectivity.
    Returns 503 with an error envelope when the database is unreachable.
    """
    try:
        async with db_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return success_response(
            data={
                "status": "healthy",
                "database": "connected",
                "environment": settings.ENVIRONMENT,
            },
        )
    except Exception:
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "data": {
                    "status": "unhealthy",
                    "database": "disconnected",
                },
                "error": {
                    "code": "DATABASE_UNAVAILABLE",
                    "message": "Database is unavailable.",
                },
                "meta": {},
            },
        )


@router.get("/version")
async def version():
    """Application version information."""
    return success_response(
        data={
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        },
    )
