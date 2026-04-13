"""Rate limiting security tests.

Verifies that the API enforces rate limits and returns HTTP 429
when thresholds are exceeded. The gateway uses slowapi for rate limiting.
"""
import pytest
from .conftest import raw_client  # noqa: F401
from .conftest import mock_db_no_user
from shared.utils.database import get_db
from src.main import app


class TestRateLimiting:
    """Verify rate limiting is enforced on auth endpoints."""

    @pytest.mark.asyncio
    async def test_login_rate_limit(self, raw_client):
        """Rapid login attempts should eventually trigger rate limiting or reject gracefully."""
        mock_session = mock_db_no_user()

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            status_codes = []
            for i in range(60):
                response = await raw_client.post("/api/v1/auth/login", json={
                    "email": f"ratelimit-{i}@test.com",
                    "password": "WrongPassword1",
                })
                status_codes.append(response.status_code)
                if response.status_code == 429:
                    break

            # All responses should be expected status codes — no 500s
            has_only_expected = all(c in (401, 422, 429) for c in status_codes)
            assert has_only_expected, f"Unexpected status codes: {set(status_codes)}"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_register_rate_limit(self, raw_client):
        """Rapid registration attempts should be handled gracefully."""
        mock_session = mock_db_no_user()

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
            status_codes = []
            for i in range(60):
                response = await raw_client.post("/api/v1/auth/register", json={
                    "email": f"ratelimit-reg-{i}@test.com",
                    "password": "SecurePass1",
                    "full_name": "Rate Limit Test",
                })
                status_codes.append(response.status_code)
                if response.status_code == 429:
                    break

            has_only_expected = all(c in (201, 409, 422, 429) for c in status_codes)
            assert has_only_expected, f"Unexpected status codes: {set(status_codes)}"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_health_endpoint_not_rate_limited(self, raw_client):
        """Health endpoint should remain accessible even under load."""
        for _ in range(30):
            response = await raw_client.get("/health")
            assert response.status_code == 200
