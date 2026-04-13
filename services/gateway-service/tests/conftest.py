"""Shared test fixtures for gateway service tests."""
import os
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Set test environment before importing app
os.environ["JWT_SECRET"] = "test-secret-key-that-is-at-least-32-characters-long-for-testing!"
os.environ["APP_ENV"] = "development"

from shared.config.settings import get_settings
get_settings.cache_clear()

from shared.utils.security import create_access_token, password_hash


def make_test_user(
    user_id=None,
    email="test@example.com",
    role="analyst",
    is_active=True,
    full_name="Test User",
):
    """Create a mock User object that behaves like an ORM User without touching SA internals."""
    user = MagicMock()
    user.id = user_id or uuid.uuid4()
    user.email = email
    user.password_hash = password_hash("TestPass1")
    user.full_name = full_name
    user.role = role
    user.organization = None
    user.is_active = is_active
    now = datetime.now(timezone.utc)
    user.created_at = now
    user.updated_at = now
    return user


def auth_headers(user_id=None, role="analyst"):
    """Generate Authorization headers for a test user."""
    uid = user_id or uuid.uuid4()
    token = create_access_token(uid, role)
    return {"Authorization": f"Bearer {token}"}
