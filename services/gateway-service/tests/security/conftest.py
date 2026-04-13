"""Shared fixtures for security tests."""
import os
import sys

# Ensure test environment is set before any imports
os.environ["JWT_SECRET"] = "test-secret-key-that-is-at-least-32-characters-long-for-testing!"
os.environ["APP_ENV"] = "development"

# Allow imports from parent tests/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.config.settings import get_settings
get_settings.cache_clear()

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, MagicMock

from src.main import app
from shared.utils.database import get_db
from conftest import make_test_user, auth_headers  # noqa: F401


def mock_db_no_user():
    """Create a mock DB session that returns no user on query."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.add = MagicMock()
    return mock_session


def mock_db_with_user(user):
    """Create a mock DB session that returns the given user on query."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_result.scalars.return_value.all.return_value = [user] if user else []
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.add = MagicMock()
    return mock_session


@pytest_asyncio.fixture
async def client():
    """Client with DB mocked to return a default analyst user for auth."""
    user = make_test_user(role="analyst")
    mock_session = mock_db_with_user(user)

    async def override_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def raw_client():
    """Client without DB mocking — for tests that manage their own overrides."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
