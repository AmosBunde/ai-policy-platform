-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users and Authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'analyst',
    organization VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

-- Regulatory Sources
CREATE TABLE regulatory_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    url TEXT NOT NULL,
    jurisdiction VARCHAR(100),
    category VARCHAR(100),
    crawl_frequency_minutes INTEGER DEFAULT 60,
    is_active BOOLEAN DEFAULT TRUE,
    last_crawled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT ck_source_type_valid CHECK (source_type IN ('rss', 'api', 'crawler', 'manual')),
    CONSTRAINT ck_crawl_frequency_positive CHECK (crawl_frequency_minutes > 0),
    CONSTRAINT ck_url_format CHECK (url ~ '^https?://')
);

-- Regulatory Documents (raw ingested)
CREATE TABLE regulatory_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID REFERENCES regulatory_sources(id),
    external_id VARCHAR(255),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) UNIQUE NOT NULL,
    url TEXT,
    published_at TIMESTAMP WITH TIME ZONE,
    jurisdiction VARCHAR(100),
    document_type VARCHAR(50),
    language VARCHAR(10) DEFAULT 'en',
    raw_metadata JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'ingested',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT ck_document_status_valid CHECK (status IN ('ingested', 'processing', 'enriched', 'failed', 'archived'))
);

CREATE INDEX idx_docs_source ON regulatory_documents(source_id);
CREATE INDEX idx_docs_status ON regulatory_documents(status);
CREATE INDEX idx_docs_jurisdiction ON regulatory_documents(jurisdiction);
CREATE INDEX idx_docs_published ON regulatory_documents(published_at DESC);
CREATE INDEX idx_docs_content_hash ON regulatory_documents(content_hash);

-- Document Enrichments (AI agent outputs)
CREATE TABLE document_enrichments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID UNIQUE REFERENCES regulatory_documents(id) ON DELETE CASCADE,
    summary TEXT,
    key_changes JSONB DEFAULT '[]',
    classification JSONB DEFAULT '{}',
    impact_scores JSONB DEFAULT '{}',
    draft_response TEXT,
    affected_entities JSONB DEFAULT '[]',
    effective_dates JSONB DEFAULT '[]',
    urgency_level VARCHAR(20) DEFAULT 'normal',
    confidence_score FLOAT DEFAULT 0.0,
    token_usage JSONB DEFAULT '{}',
    processing_time_ms INTEGER,
    agent_version VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT ck_urgency_level_valid CHECK (urgency_level IN ('low', 'normal', 'high', 'critical')),
    CONSTRAINT ck_confidence_score_range CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0)
);

CREATE INDEX idx_enrichments_urgency ON document_enrichments(urgency_level);

-- Document Embeddings (for semantic search)
CREATE TABLE document_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES regulatory_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER DEFAULT 0,
    chunk_text TEXT NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_embeddings_doc ON document_embeddings(document_id);
CREATE INDEX idx_embeddings_vector ON document_embeddings USING hnsw (embedding vector_cosine_ops);

-- Compliance Reports
CREATE TABLE compliance_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    created_by UUID REFERENCES users(id),
    document_ids JSONB DEFAULT '[]',
    report_type VARCHAR(50) DEFAULT 'standard',
    template_id VARCHAR(100),
    content JSONB DEFAULT '{}',
    file_url TEXT,
    file_format VARCHAR(10) DEFAULT 'pdf',
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT ck_report_status_valid CHECK (status IN ('draft', 'generating', 'completed', 'failed'))
);

-- Watch Rules (for notifications)
CREATE TABLE watch_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    conditions JSONB NOT NULL,
    channels JSONB DEFAULT '["email"]',
    is_active BOOLEAN DEFAULT TRUE,
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT ck_conditions_json_structure CHECK (jsonb_typeof(conditions) = 'array' OR jsonb_typeof(conditions) = 'object')
);

-- Notification Log
CREATE TABLE notification_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    watch_rule_id UUID REFERENCES watch_rules(id),
    document_id UUID REFERENCES regulatory_documents(id),
    channel VARCHAR(50) NOT NULL,
    subject TEXT,
    body TEXT,
    status VARCHAR(50) DEFAULT 'sent',
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit Log
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    details JSONB DEFAULT '{}',
    ip_address VARCHAR(45),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_action ON audit_log(action);
CREATE INDEX idx_audit_created ON audit_log(created_at DESC);

-- ── Audit Trigger Function ────────────────────────────────
-- Automatically populates audit_log on INSERT/UPDATE/DELETE for key tables.

CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (action, resource_type, resource_id, details, created_at)
        VALUES (
            TG_OP,
            TG_TABLE_NAME,
            OLD.id,
            jsonb_build_object('old', to_jsonb(OLD)),
            NOW()
        );
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (action, resource_type, resource_id, details, created_at)
        VALUES (
            TG_OP,
            TG_TABLE_NAME,
            NEW.id,
            jsonb_build_object('old', to_jsonb(OLD), 'new', to_jsonb(NEW)),
            NOW()
        );
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (action, resource_type, resource_id, details, created_at)
        VALUES (
            TG_OP,
            TG_TABLE_NAME,
            NEW.id,
            jsonb_build_object('new', to_jsonb(NEW)),
            NOW()
        );
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Attach audit triggers to key tables
CREATE TRIGGER audit_users
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER audit_regulatory_documents
    AFTER INSERT OR UPDATE OR DELETE ON regulatory_documents
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER audit_document_enrichments
    AFTER INSERT OR UPDATE OR DELETE ON document_enrichments
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER audit_compliance_reports
    AFTER INSERT OR UPDATE OR DELETE ON compliance_reports
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER audit_watch_rules
    AFTER INSERT OR UPDATE OR DELETE ON watch_rules
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- ── Row-Level Security (preparation for multi-tenant) ─────
-- Enable RLS on tables that contain user-scoped data.
-- Policies are defined but not enforced until ALTER TABLE ... FORCE ROW LEVEL SECURITY.

ALTER TABLE watch_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE compliance_reports ENABLE ROW LEVEL SECURITY;

-- Policy: users can only see their own watch rules
CREATE POLICY watch_rules_user_policy ON watch_rules
    FOR ALL
    USING (user_id = current_setting('app.current_user_id', true)::uuid)
    WITH CHECK (user_id = current_setting('app.current_user_id', true)::uuid);

-- Policy: users can only see their own notifications
CREATE POLICY notification_log_user_policy ON notification_log
    FOR ALL
    USING (user_id = current_setting('app.current_user_id', true)::uuid)
    WITH CHECK (user_id = current_setting('app.current_user_id', true)::uuid);

-- Policy: users can only see their own reports
CREATE POLICY compliance_reports_user_policy ON compliance_reports
    FOR ALL
    USING (created_by = current_setting('app.current_user_id', true)::uuid)
    WITH CHECK (created_by = current_setting('app.current_user_id', true)::uuid);

-- ── Updated Timestamp Trigger ─────────────────────────────

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at_users
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_updated_at_documents
    BEFORE UPDATE ON regulatory_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_updated_at_enrichments
    BEFORE UPDATE ON document_enrichments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_updated_at_reports
    BEFORE UPDATE ON compliance_reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ── Seed Data ─────────────────────────────────────────────
-- Default admin user (password: admin123 — change immediately in production)
INSERT INTO users (email, password_hash, full_name, role) VALUES
('admin@regulatorai.com', '$2b$12$LJ3m4ys3L3Kj5ZI6v6K9/.jQ8X8F7z9Q8U0V1Y2W3X4Z5A6B7C8D9', 'System Admin', 'admin');

-- Seed regulatory sources
INSERT INTO regulatory_sources (name, source_type, url, jurisdiction, category) VALUES
('EU AI Act Official', 'crawler', 'https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai', 'EU', 'ai_regulation'),
('US Federal Register AI', 'api', 'https://www.federalregister.gov/api/v1/documents', 'US-Federal', 'ai_regulation'),
('UK ICO AI Guidance', 'crawler', 'https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/', 'UK', 'data_protection'),
('NIST AI RMF', 'crawler', 'https://www.nist.gov/artificial-intelligence', 'US-Federal', 'ai_standards');
