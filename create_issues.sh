#!/usr/bin/env bash
# ============================================================
# RegulatorAI — GitHub Issues Creator
# Run: chmod +x scripts/create_issues.sh && ./scripts/create_issues.sh
# Prerequisites: GitHub CLI (gh) authenticated, run from repo root
# ============================================================

set -euo pipefail

# Auto-detect repo from git remote
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
if [ -z "$REPO" ]; then
  echo "❌ Could not detect repo. Make sure you are in a git repo with a GitHub remote."
  echo "   Run: gh repo view"
  exit 1
fi

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  RegulatorAI — Creating GitHub Issues & Milestones      ║"
echo "║  Repo: $REPO"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ── Create Labels ──────────────────────────────────────────
echo "📌 Creating labels..."
gh label create "backend" --color "0E8A16" --description "Backend service work" --force 2>/dev/null || true
gh label create "frontend" --color "1D76DB" --description "Frontend/UI work" --force 2>/dev/null || true
gh label create "infra" --color "D93F0B" --description "Infrastructure & DevOps" --force 2>/dev/null || true
gh label create "ai-agents" --color "7057FF" --description "LangGraph AI agent work" --force 2>/dev/null || true
gh label create "database" --color "FBCA04" --description "Database schema & migrations" --force 2>/dev/null || true
gh label create "testing" --color "BFD4F2" --description "Tests and QA" --force 2>/dev/null || true
gh label create "docs" --color "0075CA" --description "Documentation" --force 2>/dev/null || true
gh label create "security" --color "B60205" --description "Security & auth" --force 2>/dev/null || true
gh label create "search" --color "D4C5F9" --description "Search functionality" --force 2>/dev/null || true
gh label create "priority:high" --color "FF0000" --description "High priority" --force 2>/dev/null || true
gh label create "priority:medium" --color "FFA500" --description "Medium priority" --force 2>/dev/null || true
echo "✅ Labels created"

# ── Create Milestones using gh CLI ────────────────────────
echo ""
echo "🏁 Creating milestones..."

create_milestone() {
  local title="$1"
  local desc="$2"
  # Check if milestone already exists
  local existing
  existing=$(gh api "repos/${REPO}/milestones" --paginate -q ".[] | select(.title==\"${title}\") | .number" 2>/dev/null || echo "")
  if [ -n "$existing" ]; then
    echo "  ⏭️  Milestone '${title}' already exists (#${existing})"
  else
    if gh api "repos/${REPO}/milestones" \
      -f title="${title}" \
      -f description="${desc}" \
      -f state="open" \
      --silent 2>&1; then
      echo "  ✅ Created: ${title}"
    else
      echo "  ⚠️  Failed to create: ${title}"
    fi
  fi
}

create_milestone "M1: Foundation & Infrastructure" "Project scaffold, Docker, CI/CD, database schema"
create_milestone "M2: Core Backend Services" "Gateway, Ingestion, Agent service implementation"
create_milestone "M3: Search & Compliance" "Search service, compliance reports, notifications"
create_milestone "M4: Enterprise Frontend" "React dashboard, all pages, responsive design"
create_milestone "M5: Testing, Polish & Deployment" "E2E tests, load tests, production deployment"

echo ""
echo "📋 Creating issues..."
echo ""

# ══════════════════════════════════════════════════════════
# MILESTONE 1: Foundation & Infrastructure (Issues 1-5)
# ══════════════════════════════════════════════════════════

gh issue create \
  --title "Issue #1: Project scaffold, Docker Compose, and CI/CD pipeline" \
  --label "infra,priority:high" \
  --milestone "M1: Foundation & Infrastructure" \
  --body '## Description
Set up the complete project scaffold with Docker Compose for all services, GitHub Actions CI/CD pipeline, and development tooling.

## Acceptance Criteria
- [ ] All service directories created with proper structure
- [ ] `docker-compose.yml` with all services (postgres, redis, elasticsearch, 6 backend services, frontend, prometheus, grafana)
- [ ] `docker-compose.prod.yml` with production overrides
- [ ] `docker-compose.test.yml` for integration tests
- [ ] `.env.example` with all required variables documented
- [ ] GitHub Actions CI pipeline: lint, type-check, test per service
- [ ] GitHub Actions deploy pipeline (build + push images)
- [ ] All Dockerfiles optimized (multi-stage where appropriate)
- [ ] `Makefile` with common commands (up, down, test, lint, migrate)
- [ ] Pre-commit hooks config (ruff, mypy)

## Technical Notes
- Use `pgvector/pgvector:pg16` for PostgreSQL
- Redis 7 Alpine with password auth
- Elasticsearch 8.13 single-node for dev
- Each service has its own `requirements.txt`
- Shared code in `shared/` mounted into containers

## Branch
`feature/001-project-scaffold`'
echo "  ✅ Issue #1 created"

gh issue create \
  --title "Issue #2: Database schema, migrations, and seed data" \
  --label "database,backend,priority:high" \
  --milestone "M1: Foundation & Infrastructure" \
  --body '## Description
Implement the complete PostgreSQL schema with pgvector, Alembic migrations, and seed data for development.

## Acceptance Criteria
- [ ] All tables: users, regulatory_sources, regulatory_documents, document_enrichments, document_embeddings, compliance_reports, watch_rules, notification_log, audit_log
- [ ] pgvector extension with HNSW indexes
- [ ] Alembic migration setup with initial migration
- [ ] Seed script: admin user, 4+ regulatory sources, sample documents
- [ ] SQLAlchemy ORM models matching all tables
- [ ] Database connection pooling (asyncpg)
- [ ] Index optimization for common query patterns

## Branch
`feature/002-database-schema`'
echo "  ✅ Issue #2 created"

gh issue create \
  --title "Issue #3: Shared library -- Pydantic models, config, utilities" \
  --label "backend,priority:high" \
  --milestone "M1: Foundation & Infrastructure" \
  --body '## Description
Implement the shared Python library used across all backend services.

## Acceptance Criteria
- [ ] All Pydantic models: User, Document, Enrichment, Search, Report, WatchRule, Event, Auth
- [ ] Enum types: DocumentStatus, UrgencyLevel, UserRole, ReportStatus, SourceType
- [ ] Settings class with env-var loading and computed properties
- [ ] Utility functions: password hashing, JWT encode/decode, content hashing, pagination
- [ ] Redis Pub/Sub helper (publish/subscribe events)
- [ ] Structured logging setup (structlog)
- [ ] 100% test coverage on models and utils

## Branch
`feature/003-shared-library`'
echo "  ✅ Issue #3 created"

gh issue create \
  --title "Issue #4: Gateway Service -- Auth, routing, rate limiting, RBAC" \
  --label "backend,security,priority:high" \
  --milestone "M1: Foundation & Infrastructure" \
  --body '## Description
Implement the API Gateway with JWT authentication, RBAC, rate limiting, and service routing.

## Acceptance Criteria
- [ ] JWT login/register/refresh/logout endpoints
- [ ] Password hashing with bcrypt
- [ ] Role-based access control (admin, analyst, viewer)
- [ ] Rate limiting with slowapi
- [ ] Service proxy routes to all downstream services
- [ ] CORS configuration
- [ ] Request/response logging middleware
- [ ] Prometheus metrics
- [ ] OpenAPI docs with security schemes
- [ ] Health check aggregation
- [ ] Unit and integration tests

## Branch
`feature/004-gateway-service`'
echo "  ✅ Issue #4 created"

gh issue create \
  --title "Issue #5: Monitoring stack -- Prometheus, Grafana dashboards, structured logging" \
  --label "infra,priority:medium" \
  --milestone "M1: Foundation & Infrastructure" \
  --body '## Description
Set up observability: Prometheus metrics, Grafana dashboards, structured logging.

## Acceptance Criteria
- [ ] Prometheus scrape config for all services
- [ ] Grafana dashboards: service health, latency, agent pipeline metrics
- [ ] Structured logging with structlog
- [ ] Request ID propagation across services
- [ ] Alert rules: service down, error rate, latency

## Branch
`feature/005-monitoring-stack`'
echo "  ✅ Issue #5 created"

# ══════════════════════════════════════════════════════════
# MILESTONE 2: Core Backend Services (Issues 6-8)
# ══════════════════════════════════════════════════════════

gh issue create \
  --title "Issue #6: Ingestion Service -- Crawlers, parsers, Celery tasks" \
  --label "backend,priority:high" \
  --milestone "M2: Core Backend Services" \
  --body '## Description
Implement document ingestion pipeline with crawlers, parsers, and Celery async processing.

## Acceptance Criteria
- [ ] RSS feed parser, HTML extractor, PDF text extraction
- [ ] Content normalization into RegulatoryDocument schema
- [ ] SHA-256 deduplication
- [ ] Celery tasks with beat scheduling
- [ ] Source health monitoring
- [ ] Manual upload endpoint
- [ ] Redis Pub/Sub: publish document.ingested event
- [ ] Prometheus metrics and tests

## Branch
`feature/006-ingestion-service`'
echo "  ✅ Issue #6 created"

gh issue create \
  --title "Issue #7: Agent Service -- LangGraph pipeline with all agents" \
  --label "ai-agents,backend,priority:high" \
  --milestone "M2: Core Backend Services" \
  --body '## Description
Implement LangGraph multi-agent pipeline: Router, Summarizer, Classifier, Impact Ranker, Drafter, Aggregator.

## Acceptance Criteria
- [ ] LangGraph StateGraph with all nodes
- [ ] Router, Summarizer, Classifier, Impact Ranker, Drafter, Aggregator nodes
- [ ] Retry logic with exponential backoff for OpenAI
- [ ] Token usage and cost tracking
- [ ] Redis event subscription and publication
- [ ] Long document chunking
- [ ] Unit tests with mocked LLM responses

## Branch
`feature/007-agent-service`'
echo "  ✅ Issue #7 created"

gh issue create \
  --title "Issue #8: Search Service -- Elasticsearch + pgvector hybrid search" \
  --label "search,backend,priority:high" \
  --milestone "M2: Core Backend Services" \
  --body '## Description
Dual search: Elasticsearch BM25 + pgvector semantic with RRF merging.

## Acceptance Criteria
- [ ] Elasticsearch index mapping and indexing
- [ ] BM25 search with highlighting
- [ ] OpenAI embedding + pgvector cosine similarity
- [ ] Hybrid search with RRF
- [ ] Faceted filtering and autocomplete
- [ ] Tests

## Branch
`feature/008-search-service`'
echo "  ✅ Issue #8 created"

# ══════════════════════════════════════════════════════════
# MILESTONE 3: Search & Compliance (Issues 9-10)
# ══════════════════════════════════════════════════════════

gh issue create \
  --title "Issue #9: Compliance Service -- Report generation (PDF/DOCX)" \
  --label "backend,priority:medium" \
  --milestone "M3: Search & Compliance" \
  --body '## Description
Compliance report generation with Jinja2 templates, PDF and DOCX output.

## Acceptance Criteria
- [ ] 3 report templates (standard, executive, detailed)
- [ ] PDF via WeasyPrint, DOCX via python-docx
- [ ] Report versioning and compliance checklists
- [ ] File storage abstraction
- [ ] Download endpoint with auth
- [ ] Tests

## Branch
`feature/009-compliance-service`'
echo "  ✅ Issue #9 created"

gh issue create \
  --title "Issue #10: Notification Service -- Email, Slack, watch rules engine" \
  --label "backend,priority:medium" \
  --milestone "M3: Search & Compliance" \
  --body '## Description
Event-driven notifications with watch rules and multi-channel delivery.

## Acceptance Criteria
- [ ] Watch rule CRUD and matching engine
- [ ] Email (aiosmtplib), Slack (webhook), in-app notifications
- [ ] Digest scheduling
- [ ] Redis subscription to document.enriched
- [ ] Rate limiting and notification history
- [ ] Tests

## Branch
`feature/010-notification-service`'
echo "  ✅ Issue #10 created"

# ══════════════════════════════════════════════════════════
# MILESTONE 4: Enterprise Frontend (Issues 11-17)
# ══════════════════════════════════════════════════════════

gh issue create \
  --title "Issue #11: Frontend scaffold -- React 18 + TypeScript + Tailwind + routing" \
  --label "frontend,priority:high" \
  --milestone "M4: Enterprise Frontend" \
  --body '## Description
Set up React frontend with TypeScript, TailwindCSS, routing, state management, API client.

## Design Direction
Enterprise legal-tech: deep navy #0F172A, amber #F59E0B accent, DM Sans typography, glass morphism cards.

## Acceptance Criteria
- [ ] Vite + React 18 + TypeScript
- [ ] TailwindCSS enterprise theme
- [ ] React Router v6, TanStack Query, Zustand
- [ ] Axios with JWT interceptors
- [ ] Layout: sidebar, header, main content
- [ ] Dark/light theme, responsive design
- [ ] UI primitives: Button, Card, Badge, Input, Select, Modal, Toast
- [ ] Dockerfile

## Branch
`feature/011-frontend-scaffold`'
echo "  ✅ Issue #11 created"

gh issue create \
  --title "Issue #12: Auth pages -- Login, register, forgot password" \
  --label "frontend,security,priority:high" \
  --milestone "M4: Enterprise Frontend" \
  --body '## Acceptance Criteria
- [ ] Login, register, forgot password pages
- [ ] react-hook-form + zod validation
- [ ] JWT token management, protected routes
- [ ] Auth store, responsive design, tests

## Branch
`feature/012-auth-pages`'
echo "  ✅ Issue #12 created"

gh issue create \
  --title "Issue #13: Dashboard page -- Overview, stats, risk heatmap" \
  --label "frontend,priority:high" \
  --milestone "M4: Enterprise Frontend" \
  --body '## Acceptance Criteria
- [ ] 4 KPI cards, activity timeline (Recharts), risk heatmap
- [ ] Recent documents feed, quick actions
- [ ] Auto-refresh, skeleton loading

## Branch
`feature/013-dashboard-page`'
echo "  ✅ Issue #13 created"

gh issue create \
  --title "Issue #14: Document explorer -- List, detail, enrichment display" \
  --label "frontend,priority:high" \
  --milestone "M4: Enterprise Frontend" \
  --body '## Acceptance Criteria
- [ ] Document list (table + card), filter sidebar, sort
- [ ] Detail page with enrichment tabs (Summary, Changes, Classification, Impact, Draft)
- [ ] Status badges, bulk actions, URL-based filters

## Branch
`feature/014-document-explorer`'
echo "  ✅ Issue #14 created"

gh issue create \
  --title "Issue #15: Search page -- Facets, autocomplete, highlighted results" \
  --label "frontend,search,priority:high" \
  --milestone "M4: Enterprise Frontend" \
  --body '## Acceptance Criteria
- [ ] Search input with autocomplete, type toggle
- [ ] Faceted filters, result cards with highlights
- [ ] Search history, Cmd+K shortcut, URL state

## Branch
`feature/015-search-page`'
echo "  ✅ Issue #15 created"

gh issue create \
  --title "Issue #16: Reports page -- Create, list, download" \
  --label "frontend,priority:medium" \
  --milestone "M4: Enterprise Frontend" \
  --body '## Acceptance Criteria
- [ ] Report creation wizard (4 steps)
- [ ] Report list with filters, preview, download (PDF/DOCX)

## Branch
`feature/016-reports-page`'
echo "  ✅ Issue #16 created"

gh issue create \
  --title "Issue #17: Settings page -- Profile, watch rules, admin panel" \
  --label "frontend,priority:medium" \
  --milestone "M4: Enterprise Frontend" \
  --body '## Acceptance Criteria
- [ ] Profile section, watch rule builder, notification preferences
- [ ] Admin panel (users, sources, health) visible to admin role only

## Branch
`feature/017-settings-page`'
echo "  ✅ Issue #17 created"

# ══════════════════════════════════════════════════════════
# MILESTONE 5: Testing, Polish & Deployment (Issues 18-20)
# ══════════════════════════════════════════════════════════

gh issue create \
  --title "Issue #18: E2E tests, load tests, security audit" \
  --label "testing,priority:high" \
  --milestone "M5: Testing, Polish & Deployment" \
  --body '## Acceptance Criteria
- [ ] Playwright E2E tests for all major flows
- [ ] Locust load tests
- [ ] Security tests (SQL injection, XSS, RBAC)
- [ ] docker-compose.test.yml, test factories
- [ ] 80% backend / 70% frontend coverage

## Branch
`feature/018-testing-suite`'
echo "  ✅ Issue #18 created"

gh issue create \
  --title "Issue #19: Production deployment -- Kubernetes Helm, Terraform" \
  --label "infra,priority:medium" \
  --milestone "M5: Testing, Polish & Deployment" \
  --body '## Acceptance Criteria
- [ ] Helm chart, K8s manifests, HPA
- [ ] Terraform: VPC, EKS/GKE, RDS, ElastiCache, ES
- [ ] SSL/TLS, Caddy reverse proxy, DB backup CronJob

## Branch
`feature/019-production-deployment`'
echo "  ✅ Issue #19 created"

gh issue create \
  --title "Issue #20: Documentation -- API docs, user guide, runbook" \
  --label "docs,priority:medium" \
  --milestone "M5: Testing, Polish & Deployment" \
  --body '## Acceptance Criteria
- [ ] API reference, user guide, architecture docs
- [ ] CONTRIBUTING.md, CHANGELOG.md
- [ ] Troubleshooting guide, operational runbook

## Branch
`feature/020-documentation`'
echo "  ✅ Issue #20 created"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ✅ All 20 issues created successfully!                 ║"
echo "║                                                         ║"
echo "║  Milestones:                                            ║"
echo "║  M1: Foundation & Infrastructure    (Issues 1-5)        ║"
echo "║  M2: Core Backend Services          (Issues 6-8)        ║"
echo "║  M3: Search & Compliance            (Issues 9-10)       ║"
echo "║  M4: Enterprise Frontend            (Issues 11-17)      ║"
echo "║  M5: Testing, Polish & Deployment   (Issues 18-20)      ║"
echo "║                                                         ║"
echo "║  Next: Run Claude Code prompts from                     ║"
echo "║  scripts/claude_code_prompts.md                         ║"
echo "╚══════════════════════════════════════════════════════════╝"
