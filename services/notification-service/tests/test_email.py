"""Tests for email channel: rendering, header injection prevention."""
import pytest
from src.channels.email import (
    validate_email,
    sanitize_for_email,
    render_email_html,
)


class TestEmailValidation:
    def test_valid_email(self):
        assert validate_email("user@example.com") == "user@example.com"

    def test_strips_whitespace(self):
        assert validate_email("  user@test.com  ") == "user@test.com"

    def test_rejects_invalid(self):
        with pytest.raises(ValueError, match="Invalid email"):
            validate_email("not-an-email")

    def test_rejects_header_injection_newline(self):
        with pytest.raises(ValueError):
            validate_email("user@test.com\r\nBcc: evil@attacker.com")

    def test_rejects_header_injection_cr(self):
        with pytest.raises(ValueError):
            validate_email("user@test.com\rBcc: evil@attacker.com")

    def test_rejects_empty(self):
        with pytest.raises(ValueError):
            validate_email("")


class TestSanitizeForEmail:
    def test_strips_newlines(self):
        result = sanitize_for_email("Line1\r\nLine2")
        assert "\r" not in result
        assert "\n" not in result

    def test_escapes_html(self):
        result = sanitize_for_email('<script>alert("xss")</script>')
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_preserves_normal_text(self):
        assert sanitize_for_email("Normal text here") == "Normal text here"


class TestEmailRendering:
    def test_renders_html(self):
        html = render_email_html(
            title="Regulatory Alert",
            document_title="EU AI Act Update",
            summary="New compliance requirements.",
            urgency_level="high",
            rule_name="EU Privacy Watch",
        )
        assert "Regulatory Alert" in html
        assert "EU AI Act Update" in html
        assert "RegulatorAI" in html

    def test_xss_in_title_escaped(self):
        html = render_email_html(
            title='<script>alert(1)</script>Alert',
            document_title="Safe doc",
            summary="Safe summary",
            urgency_level="normal",
            rule_name="Rule",
        )
        assert "<script>" not in html

    def test_urgency_colors(self):
        html = render_email_html(
            title="Alert", document_title="Doc",
            summary="S", urgency_level="critical", rule_name="R",
        )
        assert "#e53e3e" in html  # Critical color

    def test_with_detail_url(self):
        html = render_email_html(
            title="Alert", document_title="Doc",
            summary="S", urgency_level="normal", rule_name="R",
            detail_url="https://app.regulatorai.com/doc/123",
        )
        assert "View Details" in html
