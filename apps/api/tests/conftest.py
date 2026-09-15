"""Shared test fixtures for AI Habitat API tests.

Test database isolation strategy:
  - get_engine is overridden to return an isolated in-memory SQLite engine.
  - get_session is overridden to use the same isolated engine.
  - Tests never touch the developer's normal SQLite database.
  - A separate fixture provides a simulated-failure engine for 503 tests.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from unittest.mock import AsyncMock, MagicMock

from app.core.database import Base, get_engine, get_session
from app.main import app


# ---------------------------------------------------------------------------
# F-002: Isolated test engine
# ---------------------------------------------------------------------------


@pytest.fixture
async def test_engine():
    """In-memory SQLite engine isolated from the development database.

    Creates all tables from Base.metadata so Phase 2+ tests
    can safely write data without touching the dev database.
    """
    _engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    await _engine.dispose()


@pytest.fixture
async def test_session(test_engine):
    """Async session bound to the isolated test engine.

    Available for Phase 2+ tests that need direct session access.
    """
    factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False,
    )
    async with factory() as session:
        yield session


@pytest.fixture
async def client(test_engine):
    """Async HTTP test client with fully isolated database.

    Overrides both get_engine and get_session so ALL database access
    during tests routes to the in-memory test engine.
    """
    app.dependency_overrides[get_engine] = lambda: test_engine

    async def _override_session():
        factory = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False,
        )
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# F-003: Simulated database failure
# ---------------------------------------------------------------------------


@pytest.fixture
async def client_db_unavailable():
    """Test client with a simulated database failure.

    Injects a mock engine whose connect() raises on __aenter__,
    simulating database unavailability at the infrastructure boundary.
    The REAL endpoint error-handling path is exercised.
    """
    mock_engine = MagicMock()
    mock_connect = MagicMock()
    mock_connect.__aenter__ = AsyncMock(
        side_effect=Exception("Simulated database failure"),
    )
    mock_connect.__aexit__ = AsyncMock(return_value=False)
    mock_engine.connect.return_value = mock_connect

    app.dependency_overrides[get_engine] = lambda: mock_engine

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
