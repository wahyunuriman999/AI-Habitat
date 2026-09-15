"""AI Habitat API — application entry point.

Responsibilities:
  - CORS middleware
  - Request-ID middleware
  - Exception handlers (AppError → envelope, HTTP → envelope, generic → 500)
  - Root /health (infrastructure/liveness — separate from /api/v1/health)
  - Mount the API v1 router
  - Lifecycle: verify DB on startup, dispose engine on shutdown
"""

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import api_router
from app.core.config import settings
from app.core.database import engine, get_engine
from app.core.errors import AppError
from app.core.logging import setup_logging
from app.core.middleware import RequestIdMiddleware
from app.core.response import error_response, success_response

logger = setup_logging()


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    logger.info("ai_habitat_starting")
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("database_connected")
    except Exception as exc:
        logger.error("database_connection_failed: %s", exc)
    yield
    await engine.dispose()
    logger.info("ai_habitat_stopped")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ---------------------------------------------------------------------------
# Middleware (order matters: outermost first)
# ---------------------------------------------------------------------------

app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(code=exc.code.value, message=exc.message),
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    _request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    code = {
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        422: "VALIDATION_ERROR",
    }.get(exc.status_code, "HTTP_ERROR")
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(code=code, message=str(exc.detail)),
    )


@app.exception_handler(Exception)
async def generic_error_handler(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.error("unhandled_error: %s", exc)
    return JSONResponse(
        status_code=500,
        content=error_response(
            code="INTERNAL_ERROR",
            message="An internal error occurred.",
        ),
    )


# ---------------------------------------------------------------------------
# Root health — infrastructure / liveness check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["infrastructure"])
async def liveness_check(db_engine: AsyncEngine = Depends(get_engine)):
    """Infrastructure/liveness probe.

    Performs a real ``SELECT 1`` against the database.
    Returns HTTP 503 when the database is unreachable.
    """
    try:
        async with db_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return success_response(
            data={"status": "healthy", "database": "connected"},
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


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

app.include_router(api_router, prefix="/api/v1")
