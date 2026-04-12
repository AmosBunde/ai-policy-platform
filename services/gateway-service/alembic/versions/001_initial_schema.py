"""Initial schema with all ORM models.

Revision ID: 001
Revises: None
Create Date: 2026-04-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), server_default="analyst"),
        sa.Column("organization", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # Regulatory Sources
    op.create_table(
        "regulatory_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("jurisdiction", sa.String(100), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("crawl_frequency_minutes", sa.Integer(), server_default="60"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("last_crawled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.CheckConstraint("source_type IN ('rss', 'api', 'crawler', 'manual')", name="ck_source_type_valid"),
        sa.CheckConstraint("crawl_frequency_minutes > 0", name="ck_crawl_frequency_positive"),
        sa.CheckConstraint("url ~ '^https?://'", name="ck_url_format"),
    )

    # Regulatory Documents
    op.create_table(
        "regulatory_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("regulatory_sources.id"), nullable=True),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("jurisdiction", sa.String(100), nullable=True),
        sa.Column("document_type", sa.String(50), nullable=True),
        sa.Column("language", sa.String(10), server_default="en"),
        sa.Column("raw_metadata", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(50), server_default="ingested"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.CheckConstraint("status IN ('ingested', 'processing', 'enriched', 'failed', 'archived')", name="ck_document_status_valid"),
    )
    op.create_index("idx_docs_source", "regulatory_documents", ["source_id"])
    op.create_index("idx_docs_status", "regulatory_documents", ["status"])
    op.create_index("idx_docs_jurisdiction", "regulatory_documents", ["jurisdiction"])
    op.create_index("idx_docs_published", "regulatory_documents", ["published_at"])
    op.create_index("idx_docs_content_hash", "regulatory_documents", ["content_hash"])

    # Document Enrichments
    op.create_table(
        "document_enrichments",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("regulatory_documents.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("key_changes", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb")),
        sa.Column("classification", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column("impact_scores", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column("draft_response", sa.Text(), nullable=True),
        sa.Column("affected_entities", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb")),
        sa.Column("effective_dates", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb")),
        sa.Column("urgency_level", sa.String(20), server_default="normal"),
        sa.Column("confidence_score", sa.Float(), server_default="0.0"),
        sa.Column("token_usage", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column("processing_time_ms", sa.Integer(), nullable=True),
        sa.Column("agent_version", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.CheckConstraint("urgency_level IN ('low', 'normal', 'high', 'critical')", name="ck_urgency_level_valid"),
        sa.CheckConstraint("confidence_score >= 0.0 AND confidence_score <= 1.0", name="ck_confidence_score_range"),
    )
    op.create_index("idx_enrichments_urgency", "document_enrichments", ["urgency_level"])

    # Document Embeddings
    op.create_table(
        "document_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("regulatory_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), server_default="0"),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.execute("ALTER TABLE document_embeddings ADD COLUMN embedding vector(1536)")
    op.create_index("idx_embeddings_doc", "document_embeddings", ["document_id"])
    op.execute("CREATE INDEX idx_embeddings_vector ON document_embeddings USING hnsw (embedding vector_cosine_ops)")

    # Compliance Reports
    op.create_table(
        "compliance_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("document_ids", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb")),
        sa.Column("report_type", sa.String(50), server_default="standard"),
        sa.Column("template_id", sa.String(100), nullable=True),
        sa.Column("content", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column("file_url", sa.Text(), nullable=True),
        sa.Column("file_format", sa.String(10), server_default="pdf"),
        sa.Column("status", sa.String(50), server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.CheckConstraint("status IN ('draft', 'generating', 'completed', 'failed')", name="ck_report_status_valid"),
    )

    # Watch Rules
    op.create_table(
        "watch_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("conditions", postgresql.JSONB(), nullable=False),
        sa.Column("channels", postgresql.JSONB(), server_default=sa.text("'[\"email\"]'::jsonb")),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.CheckConstraint("jsonb_typeof(conditions) = 'array' OR jsonb_typeof(conditions) = 'object'", name="ck_conditions_json_structure"),
    )

    # Notification Log
    op.create_table(
        "notification_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("watch_rule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("watch_rules.id"), nullable=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("regulatory_documents.id"), nullable=True),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), server_default="sent"),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # Audit Log
    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("details", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("idx_audit_user", "audit_log", ["user_id"])
    op.create_index("idx_audit_action", "audit_log", ["action"])
    op.create_index("idx_audit_created", "audit_log", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("notification_log")
    op.drop_table("watch_rules")
    op.drop_table("compliance_reports")
    op.drop_table("document_embeddings")
    op.drop_table("document_enrichments")
    op.drop_table("regulatory_documents")
    op.drop_table("regulatory_sources")
    op.drop_table("users")
