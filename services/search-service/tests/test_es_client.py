"""Tests for Elasticsearch client: query building, highlighting, sanitization."""
import pytest
from src.elasticsearch_client import (
    sanitize_query,
    escape_snippet,
    is_wildcard_only,
    INDEX_MAPPING,
    INDEX_NAME,
)


class TestSanitizeQuery:
    def test_strips_control_chars(self):
        assert sanitize_query("hello\x00world") == "helloworld"

    def test_strips_null_bytes(self):
        assert sanitize_query("test\x00") == "test"

    def test_limits_length(self):
        long_query = "x" * 1000
        assert len(sanitize_query(long_query)) == 500

    def test_strips_whitespace(self):
        assert sanitize_query("  hello  ") == "hello"

    def test_empty_query(self):
        assert sanitize_query("") == ""

    def test_preserves_normal_text(self):
        assert sanitize_query("AI regulation EU") == "AI regulation EU"

    def test_preserves_special_search_chars(self):
        # Elasticsearch special chars are handled by ES itself, not our sanitizer
        assert sanitize_query("GDPR AND privacy") == "GDPR AND privacy"


class TestEscapeSnippet:
    def test_escapes_html(self):
        assert "&lt;" in escape_snippet("<script>alert(1)</script>")

    def test_preserves_highlight_tags(self):
        result = escape_snippet("<em>highlighted</em> text")
        assert "<em>highlighted</em>" in result

    def test_escapes_xss_payload(self):
        result = escape_snippet('Click <a href="javascript:alert(1)">here</a>')
        assert "javascript:" not in result or "&quot;" in result

    def test_normal_text_unchanged(self):
        assert escape_snippet("plain text") == "plain text"

    def test_mixed_highlight_and_xss(self):
        result = escape_snippet('<em>good</em> <script>bad</script>')
        assert "<em>good</em>" in result
        assert "<script>" not in result


class TestWildcardOnly:
    def test_single_wildcard(self):
        assert is_wildcard_only("*") is True

    def test_multiple_wildcards(self):
        assert is_wildcard_only("***") is True

    def test_question_marks(self):
        assert is_wildcard_only("???") is True

    def test_mixed_wildcards(self):
        assert is_wildcard_only("*?*") is True

    def test_wildcard_with_text(self):
        assert is_wildcard_only("AI*") is False

    def test_normal_query(self):
        assert is_wildcard_only("GDPR regulation") is False

    def test_empty_string(self):
        assert is_wildcard_only("") is False


class TestIndexMapping:
    def test_index_has_mappings(self):
        assert "mappings" in INDEX_MAPPING

    def test_has_content_field(self):
        props = INDEX_MAPPING["mappings"]["properties"]
        assert "content" in props
        assert props["content"]["type"] == "text"

    def test_has_completion_suggest(self):
        props = INDEX_MAPPING["mappings"]["properties"]
        assert "suggest" in props
        assert props["suggest"]["type"] == "completion"

    def test_has_jurisdiction_keyword(self):
        props = INDEX_MAPPING["mappings"]["properties"]
        assert props["jurisdiction"]["type"] == "keyword"

    def test_index_name(self):
        assert INDEX_NAME == "regulatory_documents"
