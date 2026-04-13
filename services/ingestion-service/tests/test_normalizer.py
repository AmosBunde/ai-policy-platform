"""Tests for content normalizer."""
import pytest

from src.parsers.normalizer import (
    detect_language,
    generate_content_hash,
    normalize,
    _sanitize_text,
)


class TestContentHash:
    def test_deterministic(self):
        h1 = generate_content_hash("hello")
        h2 = generate_content_hash("hello")
        assert h1 == h2

    def test_different_content_different_hash(self):
        h1 = generate_content_hash("content A")
        h2 = generate_content_hash("content B")
        assert h1 != h2

    def test_sha256_length(self):
        h = generate_content_hash("test")
        assert len(h) == 64


class TestLanguageDetection:
    def test_english(self):
        text = "The quick brown fox jumps over the lazy dog. This is a test of the system."
        assert detect_language(text) == "en"

    def test_french(self):
        text = "Le chat est sur la table. Les enfants sont dans le jardin."
        assert detect_language(text) == "fr"

    def test_german(self):
        text = "Der Hund ist in der Schule. Die Kinder sind mit dem Auto."
        assert detect_language(text) == "de"

    def test_empty_defaults_to_english(self):
        assert detect_language("") == "en"


class TestSanitizeText:
    def test_strips_script_blocks(self):
        text = '<script>alert("xss")</script>Clean text'
        result = _sanitize_text(text)
        assert "alert" not in result
        assert "Clean text" in result

    def test_strips_iframe_tags(self):
        text = '<iframe src="evil.com"></iframe>Safe'
        result = _sanitize_text(text)
        assert "<iframe" not in result

    def test_preserves_plain_text(self):
        text = "Just a normal sentence."
        assert _sanitize_text(text) == text


class TestNormalize:
    def test_basic_normalization(self):
        result = normalize(
            title="Test Document",
            content="The content of the regulatory document.",
            url="https://example.com/doc",
            jurisdiction="EU",
        )
        assert result["title"] == "Test Document"
        assert result["content_hash"]
        assert len(result["content_hash"]) == 64
        assert result["language"] == "en"
        assert result["jurisdiction"] == "EU"
        assert result["status"] == "ingested"

    def test_max_content_length_enforced(self):
        long_content = "x" * 2_000_000
        result = normalize(title="Long", content=long_content)
        assert len(result["content"]) <= 1_000_000

    def test_title_max_length(self):
        long_title = "x" * 1000
        result = normalize(title=long_title, content="content")
        assert len(result["title"]) <= 500

    def test_xss_in_content_stripped(self):
        result = normalize(
            title="<script>evil()</script>Title",
            content='Normal <script>alert(1)</script> text',
        )
        assert "<script>" not in result["title"]
        assert "<script>" not in result["content"]

    def test_empty_title_gets_default(self):
        result = normalize(title="", content="content")
        assert result["title"] == "Untitled"

    def test_jurisdiction_truncated(self):
        result = normalize(title="T", content="C", jurisdiction="x" * 200)
        assert len(result["jurisdiction"]) <= 100

    def test_published_at_parsing(self):
        result = normalize(title="T", content="C", published_at="2024-01-15T10:30:00Z")
        assert result["published_at"] is not None

    def test_invalid_published_at(self):
        result = normalize(title="T", content="C", published_at="not-a-date")
        assert result["published_at"] is None
