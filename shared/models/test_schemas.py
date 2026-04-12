"""Tests for shared Pydantic models."""
import pytest
from uuid import uuid4
from datetime import datetime
from shared.models.schemas import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    RegulatoryDocumentCreate,
    DocumentEnrichmentCreate,
    ImpactScore,
    KeyChange,
    Classification,
    WatchRuleCreate,
    WatchRuleCondition,
    UserCreate,
    LoginRequest,
    DocumentEvent,
    ComplianceReportCreate,
    DocumentStatus,
    UrgencyLevel,
    UserRole,
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


class TestUserModels:
    def test_user_create(self):
        user = UserCreate(
            email="test@example.com",
            password="secure123",
            full_name="Test User",
        )
        assert user.role == UserRole.ANALYST

    def test_login_request(self):
        login = LoginRequest(email="test@example.com", password="pass")
        assert login.email == "test@example.com"


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


class TestEventModels:
    def test_document_event(self):
        event = DocumentEvent(
            event_type="document.enriched",
            document_id=uuid4(),
            metadata={"urgency": "high"},
        )
        assert event.event_type == "document.enriched"
        assert isinstance(event.timestamp, datetime)


class TestEnums:
    def test_document_status_values(self):
        assert DocumentStatus.INGESTED == "ingested"
        assert DocumentStatus.ENRICHED == "enriched"

    def test_urgency_levels(self):
        assert UrgencyLevel.CRITICAL == "critical"

    def test_user_roles(self):
        assert UserRole.ADMIN == "admin"
