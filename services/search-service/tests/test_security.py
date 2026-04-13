"""Tests for search security: query limits, wildcard rejection, XSS escaping."""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.elasticsearch_client import sanitize_query, escape_snippet, is_wildcard_only


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestQueryLengthLimit:
    def test_truncates_to_500(self):
        long_query = "a" * 600
        result = sanitize_query(long_query)
        assert len(result) == 500

    def test_sanitize_preserves_under_limit(self):
        query = "a" * 400
        assert len(sanitize_query(query)) == 400

    def test_sanitize_exact_500(self):
        query = "b" * 500
        assert len(sanitize_query(query)) == 500


class TestWildcardRejection:
    def test_wildcard_star(self):
        assert is_wildcard_only("*") is True

    def test_wildcard_question(self):
        assert is_wildcard_only("?") is True

    def test_mixed_wildcards(self):
        assert is_wildcard_only("*?*") is True

    def test_wildcard_with_text_allowed(self):
        assert is_wildcard_only("AI*") is False

    @pytest.mark.asyncio
    async def test_api_rejects_wildcard_only(self, client):
        resp = await client.post("/api/v1/search", json={
            "query": "***",
            "search_type": "keyword",
        })
        assert resp.status_code == 400
        assert "Wildcard" in resp.json()["detail"]


class TestEmptyQueryRejection:
    @pytest.mark.asyncio
    async def test_api_rejects_empty_query(self, client):
        resp = await client.post("/api/v1/search", json={
            "query": "",
            "search_type": "keyword",
        })
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_api_rejects_whitespace_query(self, client):
        resp = await client.post("/api/v1/search", json={
            "query": "   ",
            "search_type": "keyword",
        })
        assert resp.status_code == 400


class TestXSSInSearchResults:
    def test_script_tag_escaped(self):
        result = escape_snippet('<script>alert("xss")</script> result text')
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_highlight_tags_preserved(self):
        result = escape_snippet("The <em>regulation</em> requires compliance")
        assert "<em>regulation</em>" in result

    def test_event_handler_escaped(self):
        result = escape_snippet('<img src=x onerror="alert(1)"> text')
        assert 'onerror="alert(1)"' not in result

    def test_mixed_xss_and_highlights(self):
        result = escape_snippet('<em>safe</em> <script>evil</script>')
        assert "<em>safe</em>" in result
        assert "<script>" not in result


class TestControlCharStripping:
    def test_null_byte(self):
        assert "\x00" not in sanitize_query("test\x00injection")

    def test_backspace(self):
        assert "\x08" not in sanitize_query("test\x08")

    def test_bell(self):
        assert "\x07" not in sanitize_query("test\x07")


class TestIndexEndpointValidation:
    @pytest.mark.asyncio
    async def test_rejects_invalid_uuid(self, client):
        resp = await client.post("/api/v1/index/not-a-uuid", json={"title": "test"})
        assert resp.status_code == 400
        assert "Invalid document ID" in resp.json()["detail"]
