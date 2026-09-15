"""Async SQLAlchemy engine and session management.

The engine is configured via DATABASE_URL in settings.
Domain code accesses the database exclusively through SQLAlchemy —
it must never know whether the underlying store is SQLite or PostgreSQL.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# For SQLite, disable check_same_thread (aiosqlite handles threading).
# For PostgreSQL, no extra connect_args needed.
_connect_args: dict = {}
if settings.DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=(settings.ENVIRONMENT == "development"),
    connect_args=_connect_args,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models.

    Import this in every model module. Alembic's env.py uses
    Base.metadata for migration auto-generation.
    """


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a scoped async session."""
    async with async_session_factory() as session:
        yield session


def get_engine() -> AsyncEngine:
    """FastAPI dependency that provides the async database engine.

    In production this returns the module-level engine.
    Override in tests via ``app.dependency_overrides[get_engine]``
    to inject an isolated or simulated-failure engine.
    """
    return engine
