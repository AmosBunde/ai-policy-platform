-- Enable pgvector extension
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

-- Regulatory Sources
CREATE TABLE regulatory_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL, -- rss, api, crawler, manual
    url TEXT NOT NULL,
    jurisdiction VARCHAR(100),
    category VARCHAR(100),
    crawl_frequency_minutes INTEGER DEFAULT 60,
    is_active BOOLEAN DEFAULT TRUE,
    last_crawled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
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
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
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
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
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
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
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

-- Seed default admin user (password: admin123 - change immediately)
INSERT INTO users (email, password_hash, full_name, role) VALUES
('admin@regulatorai.com', '$2b$12$LJ3m4ys3L3Kj5ZI6v6K9/.jQ8X8F7z9Q8U0V1Y2W3X4Z5A6B7C8D9', 'System Admin', 'admin');

-- Seed regulatory sources
INSERT INTO regulatory_sources (name, source_type, url, jurisdiction, category) VALUES
('EU AI Act Official', 'crawler', 'https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai', 'EU', 'ai_regulation'),
('US Federal Register AI', 'api', 'https://www.federalregister.gov/api/v1/documents', 'US-Federal', 'ai_regulation'),
('UK ICO AI Guidance', 'crawler', 'https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/', 'UK', 'data_protection'),
('NIST AI RMF', 'crawler', 'https://www.nist.gov/artificial-intelligence', 'US-Federal', 'ai_standards');
