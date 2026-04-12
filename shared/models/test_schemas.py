"""Tests for shared Pydantic models."""
import pytest
from uuid import uuid4
from datetime import datetime
from pydantic import ValidationError
from shared.models.schemas import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    RegulatoryDocumentCreate,
    RegulatoryDocumentBase,
    DocumentEnrichmentCreate,
    ImpactScore,
    KeyChange,
    Classification,
    WatchRuleCreate,
    WatchRuleCondition,
    UserCreate,
    UserBase,
    UserResponse,
    LoginRequest,
    DocumentEvent,
    ComplianceReportCreate,
    DocumentStatus,
    UrgencyLevel,
    UserRole,
    sanitize_html,
)


class TestSearchModels:
    def test_search_request_defaults(self):
        req = SearchRequest(query="AI regulation")
        assert req.page == 1
        assert req.page_size == 20
        assert req.search_type == "hybrid"

    def test_search_request_with_filters(self):
        req = SearchRequest(
            query="GDPR",
            jurisdiction="EU",
            category="privacy",
            urgency_level=UrgencyLevel.HIGH,
        )
        assert req.jurisdiction == "EU"
        assert req.urgency_level == UrgencyLevel.HIGH

    def test_search_result(self):
        result = SearchResult(
            document_id=uuid4(),
            title="Test Doc",
            snippet="Some snippet",
            score=0.95,
        )
        assert result.score == 0.95
        assert result.highlights == []

    def test_search_request_empty_query_rejected(self):
        with pytest.raises(ValidationError):
            SearchRequest(query="")

    def test_search_request_query_too_long(self):
        with pytest.raises(ValidationError):
            SearchRequest(query="x" * 501)

    def test_search_request_page_size_max(self):
        req = SearchRequest(query="test", page_size=100)
        assert req.page_size == 100

    def test_search_request_page_size_over_max(self):
        with pytest.raises(ValidationError):
            SearchRequest(query="test", page_size=101)

    def test_search_request_invalid_search_type(self):
        with pytest.raises(ValidationError):
            SearchRequest(query="test", search_type="invalid")

    def test_search_request_page_zero(self):
        with pytest.raises(ValidationError):
            SearchRequest(query="test", page=0)


class TestDocumentModels:
    def test_document_create(self):
        doc = RegulatoryDocumentCreate(
            title="EU AI Act Amendment",
            content="Full text here...",
            jurisdiction="EU",
        )
        assert doc.language == "en"
        assert doc.raw_metadata == {}

    def test_enrichment_create(self):
        enrichment = DocumentEnrichmentCreate(
            document_id=uuid4(),
            summary="This regulation introduces...",
            key_changes=[
                KeyChange(change="Mandatory bias audits", affected_parties=["AI companies"]),
            ],
            classification=[
                Classification(domain="safety", confidence=0.92),
            ],
            impact_scores=[
                ImpactScore(region="EU", product_category="SaaS", score=8, justification="Direct impact"),
            ],
            urgency_level=UrgencyLevel.HIGH,
        )
        assert len(enrichment.key_changes) == 1
        assert enrichment.impact_scores[0].score == 8

    def test_impact_score_validation(self):
        with pytest.raises(Exception):
            ImpactScore(region="EU", product_category="SaaS", score=11, justification="Bad")

    def test_title_too_long(self):
        with pytest.raises(ValidationError):
            RegulatoryDocumentCreate(
                title="x" * 501,
                content="valid content",
            )

    def test_content_too_long(self):
        with pytest.raises(ValidationError):
            RegulatoryDocumentCreate(
                title="Valid Title",
                content="x" * 1_000_001,
            )

    def test_invalid_url_format(self):
        with pytest.raises(ValidationError):
            RegulatoryDocumentCreate(
                title="Test",
                content="Content",
                url="ftp://not-http.com",
            )

    def test_valid_http_url(self):
        doc = RegulatoryDocumentCreate(
            title="Test",
            content="Content",
            url="https://example.com/doc",
        )
        assert doc.url == "https://example.com/doc"

    def test_title_sanitized(self):
        doc = RegulatoryDocumentCreate(
            title='<script>alert("xss")</script>Clean Title',
            content="Safe content",
        )
        assert "<script>" not in doc.title
        assert "Clean Title" in doc.title

    def test_content_sanitized(self):
        doc = RegulatoryDocumentCreate(
            title="Title",
            content='Normal text <script>evil()</script> more text',
        )
        assert "<script>" not in doc.content

    def test_confidence_score_out_of_range(self):
        with pytest.raises(ValidationError):
            DocumentEnrichmentCreate(
                document_id=uuid4(),
                confidence_score=1.5,
            )

    def test_classification_confidence_range(self):
        with pytest.raises(ValidationError):
            Classification(domain="test", confidence=1.1)

    def test_impact_score_minimum(self):
        with pytest.raises(ValidationError):
            ImpactScore(region="EU", product_category="SaaS", score=0, justification="Bad")


class TestUserModels:
    def test_user_create(self):
        user = UserCreate(
            email="test@example.com",
            password="SecurePass1",
            full_name="Test User",
        )
        assert user.role == UserRole.ANALYST

    def test_login_request(self):
        login = LoginRequest(email="test@example.com", password="pass1234")
        assert login.email == "test@example.com"

    def test_invalid_email_format(self):
        with pytest.raises(ValidationError):
            UserCreate(
                email="not-an-email",
                password="SecurePass1",
                full_name="Test User",
            )

    def test_email_normalized_to_lowercase(self):
        user = UserCreate(
            email="Test@Example.COM",
            password="SecurePass1",
            full_name="Test User",
        )
        assert user.email == "test@example.com"

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="short",
                full_name="Test User",
            )

    def test_password_max_length(self):
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="x" * 129,
                full_name="Test User",
            )

    def test_full_name_sanitized(self):
        user = UserCreate(
            email="test@example.com",
            password="SecurePass1",
            full_name='<script>alert(1)</script>John Doe',
        )
        assert "<script>" not in user.full_name
        assert "John Doe" in user.full_name

    def test_email_max_length(self):
        with pytest.raises(ValidationError):
            UserCreate(
                email="a" * 250 + "@b.com",
                password="SecurePass1",
                full_name="Test",
            )

    def test_user_response_excludes_password(self):
        fields = UserResponse.model_fields
        assert "password_hash" not in fields
        assert "password" not in fields

    def test_organization_max_length(self):
        with pytest.raises(ValidationError):
            UserBase(
                email="test@example.com",
                full_name="Test",
                organization="x" * 256,
            )


class TestWatchRuleModels:
    def test_watch_rule_create(self):
        rule = WatchRuleCreate(
            name="EU Privacy Changes",
            conditions=[
                WatchRuleCondition(field="jurisdiction", operator="equals", value="EU"),
                WatchRuleCondition(field="category", operator="contains", value="privacy"),
            ],
            channels=["email", "slack"],
        )
        assert len(rule.conditions) == 2

    def test_invalid_operator(self):
        with pytest.raises(ValidationError):
            WatchRuleCondition(field="test", operator="invalid_op", value="val")

    def test_valid_operators(self):
        for op in ["equals", "contains", "gte", "lte"]:
            cond = WatchRuleCondition(field="test", operator=op, value="val")
            assert cond.operator == op

    def test_rule_name_sanitized(self):
        rule = WatchRuleCreate(
            name='<script>evil()</script>My Rule',
            conditions=[WatchRuleCondition(field="x", operator="equals", value="y")],
        )
        assert "<script>" not in rule.name
        assert "My Rule" in rule.name

    def test_rule_name_max_length(self):
        with pytest.raises(ValidationError):
            WatchRuleCreate(
                name="x" * 256,
                conditions=[WatchRuleCondition(field="x", operator="equals", value="y")],
            )


class TestEventModels:
    def test_document_event(self):
        event = DocumentEvent(
            event_type="document.enriched",
            document_id=uuid4(),
            metadata={"urgency": "high"},
        )
        assert event.event_type == "document.enriched"
        assert isinstance(event.timestamp, datetime)

    def test_invalid_event_type(self):
        with pytest.raises(ValidationError):
            DocumentEvent(
                event_type="invalid.event",
                document_id=uuid4(),
            )

    def test_valid_event_types(self):
        for et in ["document.ingested", "document.enriched", "document.failed", "document.archived"]:
            event = DocumentEvent(event_type=et, document_id=uuid4())
            assert event.event_type == et


class TestComplianceReportModels:
    def test_report_title_sanitized(self):
        report = ComplianceReportCreate(
            title='<script>hack()</script>Q1 Report',
            document_ids=[uuid4()],
        )
        assert "<script>" not in report.title
        assert "Q1 Report" in report.title

    def test_report_title_max_length(self):
        with pytest.raises(ValidationError):
            ComplianceReportCreate(
                title="x" * 501,
                document_ids=[uuid4()],
            )


class TestEnums:
    def test_document_status_values(self):
        assert DocumentStatus.INGESTED == "ingested"
        assert DocumentStatus.ENRICHED == "enriched"

    def test_urgency_levels(self):
        assert UrgencyLevel.CRITICAL == "critical"

    def test_user_roles(self):
        assert UserRole.ADMIN == "admin"


class TestSanitizeHtml:
    def test_script_removal(self):
        assert "<script>" not in sanitize_html('<script>alert(1)</script>')

    def test_event_handler_removal(self):
        result = sanitize_html('<div onmouseover="alert(1)">text</div>')
        assert "onmouseover" not in result

    def test_javascript_uri_removal(self):
        result = sanitize_html('javascript:void(0)')
        assert "javascript:" not in result

    def test_safe_content_preserved(self):
        text = "Normal **markdown** text with `code`"
        assert sanitize_html(text) == text
