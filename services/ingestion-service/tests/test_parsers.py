"""Tests for PDF and HTML parsers."""
import pytest

from src.parsers.html_parser import parse_html
from src.parsers.pdf_parser import parse_pdf


class TestHTMLParser:
    def test_extracts_text(self):
        html = "<html><body><p>Hello world</p></body></html>"
        result = parse_html(html)
        assert "Hello world" in result["content"]

    def test_extracts_title(self):
        html = "<html><head><title>My Title</title></head><body><p>text</p></body></html>"
        result = parse_html(html)
        assert result["title"] == "My Title"

    def test_strips_script_tags(self):
        html = '<html><body><script>alert("xss")</script><p>Safe</p></body></html>'
        result = parse_html(html)
        assert "alert" not in result["content"]
        assert "Safe" in result["content"]

    def test_strips_iframe(self):
        html = '<html><body><iframe src="evil.com"></iframe><p>Content</p></body></html>'
        result = parse_html(html)
        assert "iframe" not in result["content"]
        assert "Content" in result["content"]

    def test_strips_event_handlers(self):
        html = '<html><body><div onclick="alert(1)">Text</div></body></html>'
        result = parse_html(html)
        assert "onclick" not in str(result)

    def test_strips_javascript_uri(self):
        html = '<html><body><a href="javascript:alert(1)">Link</a></body></html>'
        result = parse_html(html)
        assert "javascript:" not in str(result)

    def test_strips_style_tags(self):
        html = "<html><body><style>body{display:none}</style><p>Visible</p></body></html>"
        result = parse_html(html)
        assert "display:none" not in result["content"]

    def test_empty_html(self):
        result = parse_html("")
        assert result["content"] == ""


class TestPDFParser:
    def test_rejects_oversized_file(self):
        huge = b"x" * (51 * 1024 * 1024)
        with pytest.raises(ValueError, match="maximum file size"):
            parse_pdf(huge)

    def test_rejects_malformed_pdf(self):
        with pytest.raises(ValueError, match="Malformed PDF"):
            parse_pdf(b"this is not a pdf")

    def test_empty_bytes_rejected(self):
        with pytest.raises(ValueError):
            parse_pdf(b"")
