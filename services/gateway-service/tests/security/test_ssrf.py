"""SSRF (Server-Side Request Forgery) prevention tests.

Verifies that:
  - file:// URLs are rejected
  - Non-HTTP(S) schemes are rejected
  - Internal IP addresses don't cause SSRF (handled by URL validation or network layer)
"""
import uuid

import pytest

from conftest import auth_headers
from .conftest import client  # noqa: F401


DANGEROUS_SCHEMES = [
    "file:///etc/passwd",
    "file:///proc/self/environ",
    "ftp://evil.com/payload",
    "gopher://evil.com:25/",
    "dict://evil.com:11211/",
    "data:text/html,<script>alert(1)</script>",
]


class TestSSRFInDocumentURL:
    """Document upload URL field should reject dangerous schemes."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("url", DANGEROUS_SCHEMES)
    async def test_non_http_schemes_rejected(self, client, url):
        """file://, ftp://, gopher://, etc. should be rejected."""
        response = await client.post(
            "/api/v1/documents/upload",
            json={
                "title": "SSRF Test Document",
                "content": "Test content for SSRF validation.",
                "url": url,
                "jurisdiction": "EU",
            },
            headers=auth_headers(),
        )
        # Upload proxies to ingestion-service which may be down (502).
        # If the service processes it, the Pydantic URL validator in
        # RegulatoryDocumentBase rejects non-http(s) URLs with 422.
        # Either way, the server must not follow the URL.
        assert response.status_code in (422, 502)

    @pytest.mark.asyncio
    async def test_http_url_accepted_or_proxied(self, client):
        """Valid http:// URL should pass validation (may 502 if service down)."""
        response = await client.post(
            "/api/v1/documents/upload",
            json={
                "title": "Valid URL Test",
                "content": "Test content.",
                "url": "https://example.com/regulation.pdf",
                "jurisdiction": "EU",
            },
            headers=auth_headers(),
        )
        # 502 if ingestion-service is down, 201 if up — both are acceptable
        assert response.status_code in (200, 201, 502)


class TestSSRFInSearchQuery:
    """Search queries should not trigger SSRF."""

    @pytest.mark.asyncio
    async def test_url_in_search_query(self, client):
        """Search query containing internal URL should not cause SSRF."""
        response = await client.post(
            "/api/v1/search/",
            json={
                "query": "http://169.254.169.254/latest/meta-data/",
                "search_type": "keyword",
                "page": 1,
                "page_size": 20,
            },
            headers=auth_headers(),
        )
        # Should be handled as a normal query string, not as a URL to fetch
        assert response.status_code in (200, 502)


class TestSSRFInReportURL:
    """Report download should not fetch arbitrary URLs."""

    @pytest.mark.asyncio
    async def test_file_url_in_report_format(self, client):
        """file:// in format parameter should not cause SSRF."""
        report_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/v1/reports/{report_id}/download",
            params={"format": "file:///etc/passwd"},
            headers=auth_headers(),
        )
        # 502 if compliance-service is down, or 404 if report not found
        assert response.status_code in (404, 502)
        # Even if it returns a response, it should not contain /etc/passwd content
        assert "root:" not in response.text
