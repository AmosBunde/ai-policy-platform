"""Tests for report generator: template rendering, PDF, DOCX."""
import pytest
from src.generator import (
    VALID_TEMPLATES,
    render_report,
    validate_template_id,
    html_to_docx,
)


class TestTemplateValidation:
    def test_valid_standard(self):
        assert validate_template_id("standard") == "standard_compliance.html"

    def test_valid_executive(self):
        assert validate_template_id("executive_summary") == "executive_summary.html"

    def test_valid_detailed(self):
        assert validate_template_id("detailed_analysis") == "detailed_analysis.html"

    def test_invalid_template_raises(self):
        with pytest.raises(ValueError, match="Invalid template"):
            validate_template_id("../../etc/passwd")

    def test_arbitrary_path_rejected(self):
        with pytest.raises(ValueError):
            validate_template_id("/etc/passwd")

    def test_empty_template_rejected(self):
        with pytest.raises(ValueError):
            validate_template_id("")

    def test_whitelist_has_three_templates(self):
        assert len(VALID_TEMPLATES) == 3


class TestRenderReport:
    def test_renders_standard_template(self):
        html = render_report(
            template_id="standard",
            title="Test Report",
            documents=[
                {
                    "title": "EU AI Act",
                    "jurisdiction": "EU",
                    "document_type": "regulation",
                    "published_at": "2024-01-15",
                    "enrichment": {
                        "summary": "New AI regulations for the EU.",
                        "key_changes": ["Mandatory bias audits"],
                        "impact_scores": [
                            {"region": "EU", "product_category": "SaaS", "score": 8, "justification": "Direct impact"}
                        ],
                        "draft_response": "We recommend compliance by Q2 2025.",
                    },
                }
            ],
        )
        assert "Test Report" in html
        assert "EU AI Act" in html
        assert "Mandatory bias audits" in html

    def test_renders_executive_summary(self):
        html = render_report(
            template_id="executive_summary",
            title="Q1 Summary",
            documents=[{"title": "Doc 1", "enrichment": {"summary": "Summary text", "urgency_level": "critical"}}],
        )
        assert "Q1 Summary" in html
        assert "Summary text" in html

    def test_renders_detailed_analysis(self):
        html = render_report(
            template_id="detailed_analysis",
            title="Deep Dive",
            documents=[{
                "title": "NIST Framework",
                "jurisdiction": "US-Federal",
                "url": "https://nist.gov/ai",
                "enrichment": {
                    "summary": "Risk management framework.",
                    "classification": [{"domain": "safety", "confidence": 0.9}],
                    "affected_entities": ["AI developers"],
                    "key_changes": ["New testing requirements"],
                    "effective_dates": ["2025-06-01"],
                    "impact_scores": [],
                    "confidence_score": 0.85,
                    "urgency_level": "high",
                    "token_usage": {"total": 5000},
                },
            }],
        )
        assert "NIST Framework" in html
        assert "safety" in html

    def test_xss_in_title_escaped(self):
        html = render_report(
            template_id="standard",
            title='<script>alert("xss")</script>Report',
            documents=[],
        )
        assert "<script>" not in html
        assert "&lt;script&gt;" in html or "alert" not in html

    def test_xss_in_document_title_escaped(self):
        html = render_report(
            template_id="standard",
            title="Safe Title",
            documents=[{"title": '<img onerror="alert(1)" src=x>', "enrichment": None}],
        )
        assert 'onerror="alert(1)"' not in html

    def test_empty_documents(self):
        html = render_report(template_id="standard", title="Empty", documents=[])
        assert "Empty" in html


class TestDocxGeneration:
    def test_generates_docx_bytes(self):
        html = "<html><body><h1>Title</h1><p>Content paragraph.</p></body></html>"
        result = html_to_docx(html, title="Test DOCX")
        assert isinstance(result, bytes)
        assert len(result) > 0
        # DOCX magic bytes (PK zip)
        assert result[:2] == b"PK"

    def test_docx_with_list(self):
        html = "<html><body><h2>Changes</h2><ul><li>Item 1</li><li>Item 2</li></ul></body></html>"
        result = html_to_docx(html)
        assert isinstance(result, bytes)

    def test_docx_with_table(self):
        html = """<html><body><h2>Impact</h2>
        <table><tr><th>Region</th><th>Score</th></tr><tr><td>EU</td><td>8</td></tr></table>
        </body></html>"""
        result = html_to_docx(html)
        assert isinstance(result, bytes)
