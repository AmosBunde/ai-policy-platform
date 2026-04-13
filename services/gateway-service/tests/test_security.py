"""Tests for security: XSS rejection, SQL injection patterns, oversized payloads."""
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from shared.utils.database import get_db
from src.main import app


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _mock_db_no_user():
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


class TestXSSInInput:
    @pytest.mark.asyncio
    async def test_xss_in_register_name(self, client):
        """Script tags should be sanitized in user-supplied fields."""
        mock_session = _mock_db_no_user()

        async def mock_refresh(obj):
            import uuid
            from datetime import datetime, timezone
            obj.id = uuid.uuid4()
            obj.created_at = datetime.now(timezone.utc)
            obj.updated_at = datetime.now(timezone.utc)
            obj.is_active = True

        mock_session.refresh = mock_refresh

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            response = await client.post("/api/v1/auth/register", json={
                "email": "xss@test.com",
                "password": "SecurePass1",
                "full_name": '<script>alert("xss")</script>Clean Name',
            })
            assert response.status_code == 201
            data = response.json()
            assert "<script>" not in data["full_name"]
            assert "Clean Name" in data["full_name"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_xss_in_login_email(self, client):
        """Even malicious email should not cause XSS."""
        mock_session = _mock_db_no_user()

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            response = await client.post("/api/v1/auth/login", json={
                "email": '<script>alert(1)</script>@test.com',
                "password": "TestPass1",
            })
            # Should fail validation or return 401, never execute script
            assert response.status_code in (401, 422)
        finally:
            app.dependency_overrides.clear()


class TestSQLInjectionPatterns:
    @pytest.mark.asyncio
    async def test_sql_injection_in_document_id(self, client):
        """SQL injection in path params should be rejected as invalid UUID."""
        response = await client.get(
            "/api/v1/documents/1'; DROP TABLE users; --",
            headers={"Authorization": "Bearer dummy"},
        )
        # Should be 400 (invalid UUID) or 401 (auth failure), never 500
        assert response.status_code in (400, 401, 403)

    @pytest.mark.asyncio
    async def test_sql_injection_in_report_id(self, client):
        response = await client.get(
            "/api/v1/reports/1 OR 1=1",
            headers={"Authorization": "Bearer dummy"},
        )
        assert response.status_code in (400, 401, 403)


class TestOversizedPayload:
    @pytest.mark.asyncio
    async def test_oversized_register_payload(self, client):
        """Reject payloads with fields exceeding max lengths."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "test@test.com",
            "password": "SecurePass1",
            "full_name": "x" * 10000,
        })
        # Should be rejected by Pydantic max_length=255
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_oversized_login_password(self, client):
        response = await client.post("/api/v1/auth/login", json={
            "email": "test@test.com",
            "password": "x" * 200,
        })
        # max_length=128 on LoginRequest.password
        assert response.status_code == 422


class TestSecurityHeaders:
    @pytest.mark.asyncio
    async def test_all_security_headers_present(self, client):
        resp = await client.get("/health")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "DENY"
        assert resp.headers.get("X-XSS-Protection") == "1; mode=block"
        assert resp.headers.get("Content-Security-Policy") == "default-src 'self'"
        assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert resp.headers.get("Permissions-Policy") == "camera=(), microphone=(), geolocation=()"
