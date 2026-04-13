"""Tests for authentication endpoints."""
import uuid
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from conftest import auth_headers, make_test_user

from shared.utils.security import create_access_token, create_refresh_token, password_hash
from src.main import app
from shared.utils.database import get_db


def _mock_db_with_user(user):
    """Create a mock DB session that returns the given user on query."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
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
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, client):
        user = make_test_user(email="login@test.com")
        mock_session = _mock_db_with_user(user)

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            response = await client.post("/api/v1/auth/login", json={
                "email": "login@test.com",
                "password": "TestPass1",
            })
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client):
        user = make_test_user()
        mock_session = _mock_db_with_user(user)

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            response = await client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "WrongPassword1",
            })
            assert response.status_code == 401
            assert response.json()["detail"] == "Invalid credentials"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, client):
        mock_session = _mock_db_with_user(None)

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            response = await client.post("/api/v1/auth/login", json={
                "email": "nobody@test.com",
                "password": "TestPass1",
            })
            assert response.status_code == 401
            # Generic message — never reveals which field is wrong
            assert response.json()["detail"] == "Invalid credentials"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, client):
        user = make_test_user(is_active=False)
        mock_session = _mock_db_with_user(user)

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            response = await client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "TestPass1",
            })
            assert response.status_code == 401
            assert response.json()["detail"] == "Invalid credentials"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_login_missing_email(self, client):
        response = await client.post("/api/v1/auth/login", json={
            "password": "testpassword"
        })
        assert response.status_code == 422


class TestRegister:
    @pytest.mark.asyncio
    async def test_register_success(self, client):
        mock_session = _mock_db_with_user(None)  # No existing user

        # Mock refresh to set attributes on whatever object is passed
        async def mock_refresh(obj):
            import uuid as uuid_mod
            from datetime import datetime, timezone
            obj.id = uuid_mod.uuid4()
            obj.created_at = datetime.now(timezone.utc)
            obj.updated_at = datetime.now(timezone.utc)
            obj.is_active = True

        mock_session.refresh = mock_refresh

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            response = await client.post("/api/v1/auth/register", json={
                "email": "new@example.com",
                "password": "SecurePass1",
                "full_name": "New User",
            })
            assert response.status_code == 201
            data = response.json()
            assert data["email"] == "new@example.com"
            assert "password_hash" not in data
            assert "password" not in data
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client):
        response = await client.post("/api/v1/auth/register", json={
            "email": "new@example.com",
            "password": "weak",
            "full_name": "New User",
        })
        # min_length=8 on the Pydantic model catches this as 422
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_no_uppercase(self, client):
        mock_session = _mock_db_with_user(None)

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            response = await client.post("/api/v1/auth/register", json={
                "email": "new@example.com",
                "password": "alllower1",
                "full_name": "New User",
            })
            assert response.status_code == 400
            assert "uppercase" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client):
        existing = make_test_user(email="existing@test.com")
        mock_session = _mock_db_with_user(existing)

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            response = await client.post("/api/v1/auth/register", json={
                "email": "existing@test.com",
                "password": "SecurePass1",
                "full_name": "Duplicate User",
            })
            assert response.status_code == 409
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_register_response_excludes_password(self, client):
        mock_session = _mock_db_with_user(None)

        async def mock_refresh(obj):
            import uuid as uuid_mod
            from datetime import datetime, timezone
            obj.id = uuid_mod.uuid4()
            obj.created_at = datetime.now(timezone.utc)
            obj.updated_at = datetime.now(timezone.utc)
            obj.is_active = True

        mock_session.refresh = mock_refresh

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            response = await client.post("/api/v1/auth/register", json={
                "email": "new2@example.com",
                "password": "SecurePass1",
                "full_name": "New User",
            })
            assert response.status_code == 201
            data = response.json()
            assert "password_hash" not in data
            assert "password" not in data
        finally:
            app.dependency_overrides.clear()


class TestRefresh:
    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, client):
        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid.token.here"
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_success(self, client):
        user = make_test_user()
        token = create_refresh_token(user.id)
        mock_session = _mock_db_with_user(user)

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            with patch("src.routes.auth._get_redis") as mock_redis_fn:
                mock_redis = AsyncMock()
                mock_redis.get = AsyncMock(return_value=None)
                mock_redis.setex = AsyncMock()
                mock_redis.close = AsyncMock()
                mock_redis_fn.return_value = mock_redis

                response = await client.post("/api/v1/auth/refresh", json={
                    "refresh_token": token
                })
                assert response.status_code == 200
                data = response.json()
                assert "access_token" in data
                assert "refresh_token" in data
        finally:
            app.dependency_overrides.clear()


class TestLogout:
    @pytest.mark.asyncio
    async def test_logout_success(self, client):
        user = make_test_user()
        token = create_refresh_token(user.id)

        with patch("src.routes.auth._get_redis") as mock_redis_fn:
            mock_redis = AsyncMock()
            mock_redis.setex = AsyncMock()
            mock_redis.close = AsyncMock()
            mock_redis_fn.return_value = mock_redis

            response = await client.post("/api/v1/auth/logout", json={
                "refresh_token": token
            })
            assert response.status_code == 200
            assert response.json()["message"] == "Logged out successfully"

    @pytest.mark.asyncio
    async def test_logout_invalid_token_still_succeeds(self, client):
        response = await client.post("/api/v1/auth/logout", json={
            "refresh_token": "invalid"
        })
        assert response.status_code == 200
