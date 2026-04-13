"""Tests for middleware: security headers, auth dependencies, role checking."""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from conftest import auth_headers, make_test_user

from shared.utils.database import get_db
from src.main import app


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestSecurityHeaders:
    @pytest.mark.asyncio
    async def test_x_content_type_options(self, client):
        resp = await client.get("/health")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"

    @pytest.mark.asyncio
    async def test_x_frame_options(self, client):
        resp = await client.get("/health")
        assert resp.headers.get("X-Frame-Options") == "DENY"

    @pytest.mark.asyncio
    async def test_x_xss_protection(self, client):
        resp = await client.get("/health")
        assert resp.headers.get("X-XSS-Protection") == "1; mode=block"

    @pytest.mark.asyncio
    async def test_referrer_policy(self, client):
        resp = await client.get("/health")
        assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    @pytest.mark.asyncio
    async def test_permissions_policy(self, client):
        resp = await client.get("/health")
        assert resp.headers.get("Permissions-Policy") == "camera=(), microphone=(), geolocation=()"

    @pytest.mark.asyncio
    async def test_csp(self, client):
        resp = await client.get("/health")
        assert resp.headers.get("Content-Security-Policy") == "default-src 'self'"

    @pytest.mark.asyncio
    async def test_request_id_header(self, client):
        resp = await client.get("/health")
        request_id = resp.headers.get("X-Request-ID")
        assert request_id is not None
        uuid.UUID(request_id)  # Should be a valid UUID


class TestAuthDependency:
    @pytest.mark.asyncio
    async def test_unauthenticated_request_rejected(self, client):
        """Protected endpoints should return 401/403 without a token."""
        resp = await client.get("/api/v1/users/me")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_invalid_bearer_token(self, client):
        resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_authenticated_request_succeeds(self, client):
        user = make_test_user()
        headers = auth_headers(user.id, user.role)

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            resp = await client.get("/api/v1/users/me", headers=headers)
            assert resp.status_code == 200
            assert resp.json()["email"] == user.email
        finally:
            app.dependency_overrides.clear()


class TestRoleChecking:
    @pytest.mark.asyncio
    async def test_admin_can_list_users(self, client):
        admin = make_test_user(role="admin")
        headers = auth_headers(admin.id, "admin")

        mock_session = AsyncMock()
        # First call: get_current_user, Second call: list_users query
        mock_result_user = MagicMock()
        mock_result_user.scalar_one_or_none.return_value = admin
        mock_result_list = MagicMock()
        mock_result_list.scalars.return_value.all.return_value = [admin]

        mock_session.execute = AsyncMock(
            side_effect=[mock_result_user, mock_result_list]
        )
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            resp = await client.get("/api/v1/users/", headers=headers)
            assert resp.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_analyst_cannot_list_users(self, client):
        analyst = make_test_user(role="analyst")
        headers = auth_headers(analyst.id, "analyst")

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = analyst
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            resp = await client.get("/api/v1/users/", headers=headers)
            assert resp.status_code == 403
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_privilege_escalation_blocked(self, client):
        """Non-admin cannot set role=admin."""
        analyst = make_test_user(role="analyst")
        headers = auth_headers(analyst.id, "analyst")

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = analyst
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            resp = await client.patch(
                f"/api/v1/users/{analyst.id}",
                json={"role": "admin"},
                headers=headers,
            )
            assert resp.status_code == 403
            assert "admin" in resp.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()
