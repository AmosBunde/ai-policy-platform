"""Tests for SQLAlchemy ORM models."""
import hashlib
import uuid
from datetime import datetime, timezone

import pytest

from shared.models.orm import (
    AuditLog,
    Base,
    ComplianceReport,
    DocumentEmbedding,
    DocumentEnrichment,
    DocumentStatusEnum,
    NotificationLog,
    RegulatoryDocument,
    RegulatorySource,
    ReportStatusEnum,
    SourceTypeEnum,
    UrgencyLevelEnum,
    User,
    UserRoleEnum,
    WatchRule,
    generate_uuid,
    utcnow,
)
from shared.models.schemas import UserResponse


class TestUserModel:
    def test_create_user(self):
        user = User(
            email="test@example.com",
            password_hash="$2b$12$hashedpassword",
            full_name="Test User",
            role=UserRoleEnum.ANALYST.value,
        )
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.role == "analyst"

    def test_user_repr_excludes_password(self):
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash="$2b$12$secret_hash_value",
            full_name="Test User",
        )
        repr_str = repr(user)
        assert "test@example.com" in repr_str
        assert "secret_hash_value" not in repr_str
        assert "password_hash" not in repr_str

    def test_password_hash_excluded_from_pydantic_response(self):
        """Ensure password_hash is NOT present in UserResponse schema fields."""
        fields = UserResponse.model_fields
        assert "password_hash" not in fields
        assert "password" not in fields

    def test_user_role_enum_values(self):
        assert UserRoleEnum.ADMIN.value == "admin"
        assert UserRoleEnum.ANALYST.value == "analyst"
        assert UserRoleEnum.VIEWER.value == "viewer"


class TestRegulatorySourceModel:
    def test_create_source(self):
        source = RegulatorySource(
            name="Test Source",
            source_type=SourceTypeEnum.RSS.value,
            url="https://example.com/feed",
            jurisdiction="EU",
            category="ai_regulation",
            crawl_frequency_minutes=60,
        )
        assert source.name == "Test Source"
        assert source.source_type == "rss"
        assert source.crawl_frequency_minutes == 60

    def test_source_type_enum_values(self):
        assert SourceTypeEnum.RSS.value == "rss"
        assert SourceTypeEnum.API.value == "api"
        assert SourceTypeEnum.CRAWLER.value == "crawler"
        assert SourceTypeEnum.MANUAL.value == "manual"

    def test_source_repr(self):
        source = RegulatorySource(
            id=uuid.uuid4(),
            name="Test Source",
            source_type="rss",
            url="https://example.com",
        )
        repr_str = repr(source)
        assert "Test Source" in repr_str
        assert "rss" in repr_str


class TestRegulatoryDocumentModel:
    def test_create_document(self):
        content = "Test document content"
        doc = RegulatoryDocument(
            title="Test Doc",
            content=content,
            content_hash=RegulatoryDocument.compute_content_hash(content),
            status=DocumentStatusEnum.INGESTED.value,
        )
        assert doc.title == "Test Doc"
        assert doc.status == "ingested"
        assert len(doc.content_hash) == 64

    def test_content_hash_uses_sha256(self):
        content = "Test content for hashing"
        computed_hash = RegulatoryDocument.compute_content_hash(content)
        expected_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        assert computed_hash == expected_hash
        assert len(computed_hash) == 64

    def test_content_hash_deterministic(self):
        content = "Same content"
        hash1 = RegulatoryDocument.compute_content_hash(content)
        hash2 = RegulatoryDocument.compute_content_hash(content)
        assert hash1 == hash2

    def test_different_content_different_hash(self):
        hash1 = RegulatoryDocument.compute_content_hash("content A")
        hash2 = RegulatoryDocument.compute_content_hash("content B")
        assert hash1 != hash2

    def test_document_status_enum_values(self):
        assert DocumentStatusEnum.INGESTED.value == "ingested"
        assert DocumentStatusEnum.PROCESSING.value == "processing"
        assert DocumentStatusEnum.ENRICHED.value == "enriched"
        assert DocumentStatusEnum.FAILED.value == "failed"
        assert DocumentStatusEnum.ARCHIVED.value == "archived"


class TestDocumentEnrichmentModel:
    def test_create_enrichment(self):
        enrichment = DocumentEnrichment(
            document_id=uuid.uuid4(),
            summary="Test summary",
            urgency_level=UrgencyLevelEnum.HIGH.value,
            confidence_score=0.85,
        )
        assert enrichment.summary == "Test summary"
        assert enrichment.urgency_level == "high"
        assert enrichment.confidence_score == 0.85

    def test_urgency_level_enum_values(self):
        assert UrgencyLevelEnum.LOW.value == "low"
        assert UrgencyLevelEnum.NORMAL.value == "normal"
        assert UrgencyLevelEnum.HIGH.value == "high"
        assert UrgencyLevelEnum.CRITICAL.value == "critical"


class TestDocumentEmbeddingModel:
    def test_create_embedding(self):
        embedding = DocumentEmbedding(
            document_id=uuid.uuid4(),
            chunk_index=0,
            chunk_text="Sample chunk text",
        )
        assert embedding.chunk_index == 0
        assert embedding.chunk_text == "Sample chunk text"


class TestComplianceReportModel:
    def test_create_report(self):
        report = ComplianceReport(
            title="Q1 Compliance Report",
            report_type="standard",
            status=ReportStatusEnum.DRAFT.value,
        )
        assert report.title == "Q1 Compliance Report"
        assert report.status == "draft"

    def test_report_status_enum_values(self):
        assert ReportStatusEnum.DRAFT.value == "draft"
        assert ReportStatusEnum.GENERATING.value == "generating"
        assert ReportStatusEnum.COMPLETED.value == "completed"
        assert ReportStatusEnum.FAILED.value == "failed"


class TestWatchRuleModel:
    def test_create_watch_rule(self):
        rule = WatchRule(
            user_id=uuid.uuid4(),
            name="EU AI Watch",
            conditions=[{"field": "jurisdiction", "operator": "equals", "value": "EU"}],
            channels=["email", "slack"],
        )
        assert rule.name == "EU AI Watch"
        assert rule.is_active is None  # Not set via default in Python, uses server_default

    def test_watch_rule_repr(self):
        rule = WatchRule(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name="Test Rule",
            conditions=[],
        )
        assert "Test Rule" in repr(rule)


class TestNotificationLogModel:
    def test_create_notification(self):
        notif = NotificationLog(
            user_id=uuid.uuid4(),
            channel="email",
            subject="New regulation alert",
            status="sent",
        )
        assert notif.channel == "email"
        assert notif.status == "sent"


class TestAuditLogModel:
    def test_create_audit_log(self):
        log = AuditLog(
            user_id=uuid.uuid4(),
            action="CREATE",
            resource_type="regulatory_documents",
            resource_id=uuid.uuid4(),
            ip_address="192.168.1.1",
        )
        assert log.action == "CREATE"
        assert log.resource_type == "regulatory_documents"
        assert log.ip_address == "192.168.1.1"

    def test_audit_log_repr(self):
        log = AuditLog(
            id=uuid.uuid4(),
            action="UPDATE",
            resource_type="users",
        )
        repr_str = repr(log)
        assert "UPDATE" in repr_str
        assert "users" in repr_str


class TestHelpers:
    def test_utcnow_returns_timezone_aware(self):
        now = utcnow()
        assert now.tzinfo is not None
        assert now.tzinfo == timezone.utc

    def test_generate_uuid_returns_uuid4(self):
        uid = generate_uuid()
        assert isinstance(uid, uuid.UUID)
        assert uid.version == 4

    def test_generate_uuid_is_unique(self):
        uid1 = generate_uuid()
        uid2 = generate_uuid()
        assert uid1 != uid2


class TestBaseMetadata:
    def test_all_tables_registered(self):
        table_names = set(Base.metadata.tables.keys())
        expected = {
            "users",
            "regulatory_sources",
            "regulatory_documents",
            "document_enrichments",
            "document_embeddings",
            "compliance_reports",
            "watch_rules",
            "notification_log",
            "audit_log",
        }
        assert expected.issubset(table_names)
