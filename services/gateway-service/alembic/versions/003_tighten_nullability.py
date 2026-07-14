"""Align column nullability with the ORM models.

The initial schema (001, mirroring the legacy init.sql) left columns with
server defaults as nullable, while the ORM models in shared/models/orm.py
declare them non-optional. `alembic check` (now enforced in CI) flagged
every one of these. All columns carry server defaults, so SET NOT NULL is
safe on any database that has only ever been written through the app.

Revision ID: 003
Revises: 002
"""

from typing import Union

from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels = None
depends_on = None

_NOT_NULL_COLUMNS: dict[str, tuple[str, ...]] = {
    "audit_log": ("details", "created_at"),
    "compliance_reports": (
        "document_ids",
        "report_type",
        "content",
        "file_format",
        "status",
        "created_at",
        "updated_at",
    ),
    "document_embeddings": ("chunk_index", "created_at"),
    "document_enrichments": (
        "key_changes",
        "classification",
        "impact_scores",
        "affected_entities",
        "effective_dates",
        "urgency_level",
        "confidence_score",
        "token_usage",
        "created_at",
        "updated_at",
    ),
    "notification_log": ("status", "sent_at"),
    "regulatory_documents": (
        "language",
        "raw_metadata",
        "status",
        "created_at",
        "updated_at",
    ),
    "regulatory_sources": ("crawl_frequency_minutes", "is_active", "created_at"),
    "users": ("role", "is_active", "created_at", "updated_at"),
    "watch_rules": ("channels", "is_active", "created_at"),
}


def upgrade() -> None:
    for table, columns in _NOT_NULL_COLUMNS.items():
        for column in columns:
            # Backfill any legacy NULLs from the column's server default
            # before tightening; DEFAULT here resolves that default.
            # Identifiers come from the hardcoded map above, not user input.
            op.execute(
                f"UPDATE {table} SET {column} = DEFAULT WHERE {column} IS NULL"  # nosec B608
            )
            op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} SET NOT NULL")


def downgrade() -> None:
    for table, columns in _NOT_NULL_COLUMNS.items():
        for column in columns:
            op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} DROP NOT NULL")  # noqa: E501
