"""Triggers and row-level security, ported from the legacy init.sql.

Migrations are the single source of truth for schema (issue #86);
init.sql now only creates extensions. This revision carries everything
init.sql previously did beyond bare tables:

- updated_at maintenance triggers (users, regulatory_documents,
  document_enrichments, compliance_reports)
- audit_log population triggers on key tables
- RLS enablement + per-user policies (defined but not FORCEd yet)

Revision ID: 002
Revises: 001
"""

from typing import Union

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels = None
depends_on = None

_AUDIT_TABLES = (
    "users",
    "regulatory_documents",
    "document_enrichments",
    "compliance_reports",
    "watch_rules",
)

_UPDATED_AT = {
    "set_updated_at_users": "users",
    "set_updated_at_documents": "regulatory_documents",
    "set_updated_at_enrichments": "document_enrichments",
    "set_updated_at_reports": "compliance_reports",
}

_RLS_POLICIES = {
    "watch_rules_user_policy": ("watch_rules", "user_id"),
    "notification_log_user_policy": ("notification_log", "user_id"),
    "compliance_reports_user_policy": ("compliance_reports", "created_by"),
}


def upgrade() -> None:
    # ── updated_at maintenance ────────────────────────────
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    for trigger, table in _UPDATED_AT.items():
        op.execute(
            f"""
            CREATE TRIGGER {trigger}
                BEFORE UPDATE ON {table}
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            """
        )

    # ── audit log ─────────────────────────────────────────
    op.execute(
        """
        CREATE OR REPLACE FUNCTION audit_trigger_func()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                INSERT INTO audit_log
                    (action, resource_type, resource_id, details, created_at)
                VALUES (TG_OP, TG_TABLE_NAME, OLD.id,
                        jsonb_build_object('old', to_jsonb(OLD)), NOW());
                RETURN OLD;
            ELSIF TG_OP = 'UPDATE' THEN
                INSERT INTO audit_log
                    (action, resource_type, resource_id, details, created_at)
                VALUES (TG_OP, TG_TABLE_NAME, NEW.id,
                        jsonb_build_object(
                            'old', to_jsonb(OLD), 'new', to_jsonb(NEW)), NOW());
                RETURN NEW;
            ELSIF TG_OP = 'INSERT' THEN
                INSERT INTO audit_log
                    (action, resource_type, resource_id, details, created_at)
                VALUES (TG_OP, TG_TABLE_NAME, NEW.id,
                        jsonb_build_object('new', to_jsonb(NEW)), NOW());
                RETURN NEW;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    for table in _AUDIT_TABLES:
        op.execute(
            f"""
            CREATE TRIGGER audit_{table}
                AFTER INSERT OR UPDATE OR DELETE ON {table}
                FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
            """
        )

    # ── row-level security (multi-tenant preparation) ─────
    for policy, (table, column) in _RLS_POLICIES.items():
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(
            f"""
            CREATE POLICY {policy} ON {table}
                FOR ALL
                USING ({column} = current_setting('app.current_user_id', true)::uuid)
                WITH CHECK ({column} = current_setting('app.current_user_id', true)::uuid);
            """
        )


def downgrade() -> None:
    for policy, (table, _column) in _RLS_POLICIES.items():
        op.execute(f"DROP POLICY IF EXISTS {policy} ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
    for table in _AUDIT_TABLES:
        op.execute(f"DROP TRIGGER IF EXISTS audit_{table} ON {table};")
    op.execute("DROP FUNCTION IF EXISTS audit_trigger_func();")
    for trigger, table in _UPDATED_AT.items():
        op.execute(f"DROP TRIGGER IF EXISTS {trigger} ON {table};")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
