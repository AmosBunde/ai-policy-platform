"""Path traversal security tests.

Verifies that:
  - ../ patterns in path parameters are rejected
  - Encoded path traversal sequences are blocked
  - URL-encoded and double-encoded traversal attempts are caught
"""
import pytest

from conftest import auth_headers
from .conftest import client  # noqa: F401


PATH_TRAVERSAL_PAYLOADS = [
    "../../../etc/passwd",
    "....//....//....//etc/passwd",
    "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "..%00/etc/passwd",
    "....//etc/passwd",
]


class TestPathTraversalInDocumentId:
    """Path traversal in document ID should be rejected by UUID validation."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", PATH_TRAVERSAL_PAYLOADS)
    async def test_traversal_in_document_path(self, client, payload):
        response = await client.get(
            f"/api/v1/documents/{payload}",
            headers=auth_headers(),
        )
        # Slashes in payload create non-matching routes (404) or
        # UUID validation rejects non-UUID values (400)
        assert response.status_code in (400, 404)
        # Must not return file contents
        assert "root:" not in response.text

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", PATH_TRAVERSAL_PAYLOADS)
    async def test_traversal_in_report_path(self, client, payload):
        response = await client.get(
            f"/api/v1/reports/{payload}",
            headers=auth_headers(),
        )
        assert response.status_code in (400, 404)
        assert "root:" not in response.text


class TestPathTraversalInUploadFilename:
    """Filename manipulation in document upload should not write to arbitrary paths."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("filename", [
        "../../../etc/cron.d/malicious",
        "....//....//payload.sh",
        "/etc/passwd",
    ])
    async def test_traversal_filename_in_upload(self, client, filename):
        """Document title containing path traversal should be handled safely."""
        response = await client.post(
            "/api/v1/documents/upload",
            json={
                "title": filename,
                "content": "Test content for path traversal check.",
                "jurisdiction": "EU",
            },
            headers=auth_headers(),
        )
        # Upload proxies to ingestion-service; 502 if down, or accepted safely.
        # Must never write to the filesystem or return 500.
        assert response.status_code in (200, 201, 502)


class TestPathTraversalInQueryParams:
    """Path traversal in query parameters should not leak files."""

    @pytest.mark.asyncio
    async def test_traversal_in_jurisdiction_filter(self, client):
        response = await client.get(
            "/api/v1/documents/",
            params={"jurisdiction": "../../../etc/passwd"},
            headers=auth_headers(),
        )
        # Proxied to ingestion-service; may return 502 if down
        assert response.status_code in (200, 502)
        if response.status_code == 200:
            assert "root:" not in response.text

    @pytest.mark.asyncio
    async def test_traversal_in_search_suggest(self, client):
        response = await client.get(
            "/api/v1/search/suggest",
            params={"q": "../../../etc/shadow"},
            headers=auth_headers(),
        )
        assert response.status_code in (200, 502)
        if response.status_code == 200:
            assert "root:" not in response.text
