"""SQL injection security tests.

Verifies that common SQLi payloads are rejected across all endpoints.
The gateway uses parameterized queries via SQLAlchemy ORM and UUID
validation on path parameters, so injection should be impossible.
"""
import pytest
from conftest import auth_headers

from .conftest import client  # noqa: F401 — pytest fixture


# Classic SQLi payloads
SQL_PAYLOADS = [
    "1'; DROP TABLE users; --",
    "1 OR 1=1",
    "1' UNION SELECT * FROM users --",
    "1; SELECT pg_sleep(5) --",
    "' OR ''='",
    "1' AND 1=CONVERT(int, (SELECT @@version)) --",
    "admin'--",
    "1' WAITFOR DELAY '0:0:5' --",
    "1%27%20OR%201%3D1",
    "1' OR '1'='1' /*",
    "-1 UNION SELECT username, password FROM users --",
]


class TestSQLInjectionInDocuments:
    """SQLi in document ID path parameter — should be rejected as invalid UUID."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", SQL_PAYLOADS[:8])
    async def test_sqli_in_document_id(self, client, payload):
        response = await client.get(
            f"/api/v1/documents/{payload}",
            headers=auth_headers(),
        )
        # Must be 400 (invalid UUID format) — never 500 (server error)
        assert response.status_code == 400
        assert "Invalid document ID" in response.json().get("detail", "")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", SQL_PAYLOADS[:8])
    async def test_sqli_in_enrichment_id(self, client, payload):
        response = await client.get(
            f"/api/v1/documents/{payload}/enrichment",
            headers=auth_headers(),
        )
        assert response.status_code == 400


class TestSQLInjectionInReports:
    """SQLi in report ID path parameter."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", SQL_PAYLOADS[:8])
    async def test_sqli_in_report_id(self, client, payload):
        response = await client.get(
            f"/api/v1/reports/{payload}",
            headers=auth_headers(),
        )
        assert response.status_code == 400
        assert "Invalid report ID" in response.json().get("detail", "")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", SQL_PAYLOADS[:8])
    async def test_sqli_in_report_download(self, client, payload):
        response = await client.get(
            f"/api/v1/reports/{payload}/download",
            headers=auth_headers(),
        )
        assert response.status_code == 400


class TestSQLInjectionInUsers:
    """SQLi in user ID path parameter."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", SQL_PAYLOADS[:5])
    async def test_sqli_in_user_id(self, client, payload):
        response = await client.patch(
            f"/api/v1/users/{payload}",
            json={"full_name": "Test"},
            headers=auth_headers(),
        )
        assert response.status_code == 400
        assert "Invalid user ID" in response.json().get("detail", "")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", SQL_PAYLOADS[:5])
    async def test_sqli_in_user_delete(self, client, payload):
        response = await client.delete(
            f"/api/v1/users/{payload}",
            headers=auth_headers(role="admin"),
        )
        # Returns 400 (invalid UUID) or 403 (non-admin in test env)
        assert response.status_code in (400, 403)


class TestSQLInjectionInSearch:
    """SQLi in search query body."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", SQL_PAYLOADS[:5])
    async def test_sqli_in_search_query(self, client, payload):
        response = await client.post(
            "/api/v1/search/",
            json={"query": payload, "search_type": "keyword", "page": 1, "page_size": 20},
            headers=auth_headers(),
        )
        # Search proxies to search-service; may return 502 if service is down.
        # Must never return 500 (internal error indicating SQL injection success).
        assert response.status_code in (200, 502)
        # If 200, the response should not contain database errors
        if response.status_code == 200:
            text = response.text.lower()
            assert "syntax error" not in text
            assert "pg_catalog" not in text

    @pytest.mark.asyncio
    async def test_sqli_in_search_suggest(self, client):
        response = await client.get(
            "/api/v1/search/suggest",
            params={"q": "' OR 1=1 --"},
            headers=auth_headers(),
        )
        assert response.status_code in (200, 502)
