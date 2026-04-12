"""SQLAlchemy 2.0 ORM models for RegulatorAI."""
import enum
import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> uuid.UUID:
    return uuid.uuid4()


# ── Enums ──────────────────────────────────────────────────

class UserRoleEnum(str, enum.Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class SourceTypeEnum(str, enum.Enum):
    RSS = "rss"
    API = "api"
    CRAWLER = "crawler"
    MANUAL = "manual"


class DocumentStatusEnum(str, enum.Enum):
    INGESTED = "ingested"
    PROCESSING = "processing"
    ENRICHED = "enriched"
    FAILED = "failed"
    ARCHIVED = "archived"


class UrgencyLevelEnum(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class ReportStatusEnum(str, enum.Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


# ── Users ──────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid,
        server_default=text("uuid_generate_v4()"),
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True,
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default=UserRoleEnum.ANALYST.value)
    organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=text("NOW()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=text("NOW()"),
        onupdate=utcnow,
    )

    # Relationships
    watch_rules: Mapped[list["WatchRule"]] = relationship(
        back_populates="user", cascade="all, delete-orphan",
    )
    compliance_reports: Mapped[list["ComplianceReport"]] = relationship(
        back_populates="created_by_user",
    )
    notifications: Mapped[list["NotificationLog"]] = relationship(
        back_populates="user",
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


# ── Regulatory Sources ─────────────────────────────────────

class RegulatorySource(Base):
    __tablename__ = "regulatory_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid,
        server_default=text("uuid_generate_v4()"),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    jurisdiction: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    crawl_frequency_minutes: Mapped[int] = mapped_column(Integer, default=60)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_crawled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=text("NOW()"),
    )

    # Relationships
    documents: Mapped[list["RegulatoryDocument"]] = relationship(
        back_populates="source",
    )

    __table_args__ = (
        CheckConstraint(
            "source_type IN ('rss', 'api', 'crawler', 'manual')",
            name="ck_source_type_valid",
        ),
        CheckConstraint(
            "crawl_frequency_minutes > 0",
            name="ck_crawl_frequency_positive",
        ),
        CheckConstraint(
            "url ~ '^https?://'",
            name="ck_url_format",
        ),
    )

    def __repr__(self) -> str:
        return f"<RegulatorySource(id={self.id}, name={self.name}, type={self.source_type})>"


# ── Regulatory Documents ───────────────────────────────────

class RegulatoryDocument(Base):
    __tablename__ = "regulatory_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid,
        server_default=text("uuid_generate_v4()"),
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regulatory_sources.id"), nullable=True,
    )
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False,
    )
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    jurisdiction: Mapped[str | None] = mapped_column(String(100), nullable=True)
    document_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en")
    raw_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))
    status: Mapped[str] = mapped_column(
        String(50), default=DocumentStatusEnum.INGESTED.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=text("NOW()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=text("NOW()"),
        onupdate=utcnow,
    )

    # Relationships
    source: Mapped["RegulatorySource | None"] = relationship(
        back_populates="documents",
    )
    enrichment: Mapped["DocumentEnrichment | None"] = relationship(
        back_populates="document", uselist=False, cascade="all, delete-orphan",
    )
    embeddings: Mapped[list["DocumentEmbedding"]] = relationship(
        back_populates="document", cascade="all, delete-orphan",
    )
    notifications: Mapped[list["NotificationLog"]] = relationship(
        back_populates="document",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('ingested', 'processing', 'enriched', 'failed', 'archived')",
            name="ck_document_status_valid",
        ),
        Index("idx_docs_source", "source_id"),
        Index("idx_docs_status", "status"),
        Index("idx_docs_jurisdiction", "jurisdiction"),
        Index("idx_docs_published", "published_at", postgresql_using="btree"),
        Index("idx_docs_content_hash", "content_hash"),
    )

    @staticmethod
    def compute_content_hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def __repr__(self) -> str:
        return f"<RegulatoryDocument(id={self.id}, title={self.title[:50] if self.title else ''})>"


# ── Document Enrichments ───────────────────────────────────

class DocumentEnrichment(Base):
    __tablename__ = "document_enrichments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid,
        server_default=text("uuid_generate_v4()"),
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("regulatory_documents.id", ondelete="CASCADE"),
        unique=True, nullable=False,
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_changes: Mapped[dict] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"))
    classification: Mapped[dict] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))
    impact_scores: Mapped[dict] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))
    draft_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    affected_entities: Mapped[dict] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"))
    effective_dates: Mapped[dict] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"))
    urgency_level: Mapped[str] = mapped_column(
        String(20), default=UrgencyLevelEnum.NORMAL.value,
    )
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    token_usage: Mapped[dict] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    agent_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=text("NOW()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=text("NOW()"),
        onupdate=utcnow,
    )

    # Relationships
    document: Mapped["RegulatoryDocument"] = relationship(
        back_populates="enrichment",
    )

    __table_args__ = (
        CheckConstraint(
            "urgency_level IN ('low', 'normal', 'high', 'critical')",
            name="ck_urgency_level_valid",
        ),
        CheckConstraint(
            "confidence_score >= 0.0 AND confidence_score <= 1.0",
            name="ck_confidence_score_range",
        ),
        Index("idx_enrichments_urgency", "urgency_level"),
    )

    def __repr__(self) -> str:
        return f"<DocumentEnrichment(id={self.id}, document_id={self.document_id})>"


# ── Document Embeddings ────────────────────────────────────

class DocumentEmbedding(Base):
    __tablename__ = "document_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid,
        server_default=text("uuid_generate_v4()"),
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("regulatory_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    # Vector column is defined in raw SQL via init.sql / migration
    # SQLAlchemy doesn't natively support pgvector; the column exists in the DB
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=text("NOW()"),
    )

    # Relationships
    document: Mapped["RegulatoryDocument"] = relationship(
        back_populates="embeddings",
    )

    __table_args__ = (
        Index("idx_embeddings_doc", "document_id"),
    )

    def __repr__(self) -> str:
        return f"<DocumentEmbedding(id={self.id}, document_id={self.document_id}, chunk={self.chunk_index})>"


# ── Compliance Reports ─────────────────────────────────────

class ComplianceReport(Base):
    __tablename__ = "compliance_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid,
        server_default=text("uuid_generate_v4()"),
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True,
    )
    document_ids: Mapped[dict] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"))
    report_type: Mapped[str] = mapped_column(String(50), default="standard")
    template_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    content: Mapped[dict] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))
    file_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_format: Mapped[str] = mapped_column(String(10), default="pdf")
    status: Mapped[str] = mapped_column(
        String(50), default=ReportStatusEnum.DRAFT.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=text("NOW()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=text("NOW()"),
        onupdate=utcnow,
    )

    # Relationships
    created_by_user: Mapped["User | None"] = relationship(
        back_populates="compliance_reports",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'generating', 'completed', 'failed')",
            name="ck_report_status_valid",
        ),
    )

    def __repr__(self) -> str:
        return f"<ComplianceReport(id={self.id}, title={self.title[:50] if self.title else ''})>"


# ── Watch Rules ────────────────────────────────────────────

class WatchRule(Base):
    __tablename__ = "watch_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid,
        server_default=text("uuid_generate_v4()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    conditions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    channels: Mapped[dict] = mapped_column(JSONB, default=list, server_default=text("'[\"email\"]'::jsonb"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=text("NOW()"),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="watch_rules")
    notifications: Mapped[list["NotificationLog"]] = relationship(
        back_populates="watch_rule",
    )

    __table_args__ = (
        CheckConstraint(
            "jsonb_typeof(conditions) = 'array' OR jsonb_typeof(conditions) = 'object'",
            name="ck_conditions_json_structure",
        ),
    )

    def __repr__(self) -> str:
        return f"<WatchRule(id={self.id}, name={self.name})>"


# ── Notification Log ───────────────────────────────────────

class NotificationLog(Base):
    __tablename__ = "notification_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid,
        server_default=text("uuid_generate_v4()"),
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True,
    )
    watch_rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("watch_rules.id"), nullable=True,
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regulatory_documents.id"), nullable=True,
    )
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    subject: Mapped[str | None] = mapped_column(Text, nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="sent")
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=text("NOW()"),
    )

    # Relationships
    user: Mapped["User | None"] = relationship(back_populates="notifications")
    watch_rule: Mapped["WatchRule | None"] = relationship(
        back_populates="notifications",
    )
    document: Mapped["RegulatoryDocument | None"] = relationship(
        back_populates="notifications",
    )

    def __repr__(self) -> str:
        return f"<NotificationLog(id={self.id}, channel={self.channel}, status={self.status})>"


# ── Audit Log ──────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid,
        server_default=text("uuid_generate_v4()"),
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True,
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
    )
    details: Mapped[dict] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=text("NOW()"),
    )

    # Relationships
    user: Mapped["User | None"] = relationship(back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_action", "action"),
        Index("idx_audit_created", "created_at", postgresql_using="btree"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, resource={self.resource_type})>"
