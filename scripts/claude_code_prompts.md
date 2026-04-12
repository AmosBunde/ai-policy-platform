# RegulatorAI — Claude Code Implementation Prompts

> **How to use**: Copy each prompt below into Claude Code (`claude` CLI) one at a time.
> Each prompt will: implement the issue → create a detailed git commit → create a PR → merge to main → close the issue.
>
> **Prerequisites**:
> 1. Run `./scripts/create_issues.sh` first to create all GitHub issues
> 2. Ensure `gh` CLI is authenticated
> 3. Ensure you are in the repo root directory
> 4. Have Claude Code installed: `npm install -g @anthropic-ai/claude-code`

---

## Pre-flight: Initialize the repo

```bash
# Run this ONCE before starting the issues
cd regulatorai
git init
git remote add origin git@github.com:your-org/regulatorai.git
git add .
git commit -m "chore: initial project scaffold with architecture docs and Docker infrastructure"
git push -u origin main
```

---

## Issue #1: Project scaffold, Docker Compose, and CI/CD pipeline

```
Implement GitHub Issue #1: Project scaffold, Docker Compose, and CI/CD pipeline.

Context: You are in the root of the `regulatorai` repo. The scaffold already exists with docker-compose.yml, .env.example, Dockerfiles, and .github/workflows/ci.yml.

Tasks:
1. Review and enhance the existing docker-compose.yml — ensure all healthchecks work, volumes are correct, network is consistent
2. Create docker-compose.prod.yml with production overrides (replicas, restart policies, resource limits, no port exposure except gateway)
3. Create docker-compose.test.yml for integration testing (ephemeral volumes, test env vars)
4. Create a Makefile with targets: up, down, build, test, lint, migrate, seed, logs, clean
5. Create .pre-commit-config.yaml with ruff and mypy hooks
6. Verify all Dockerfiles build successfully
7. Ensure the CI pipeline in .github/workflows/ci.yml is complete and correct

After implementation:
- git checkout -b feature/001-project-scaffold
- git add -A
- git commit with this EXACT format:
  "feat(infra): implement project scaffold with Docker Compose and CI/CD pipeline

  - Configure multi-service Docker Compose with healthchecks and dependency ordering
  - Add production compose overrides with resource limits and restart policies
  - Add test compose with ephemeral volumes for integration testing
  - Create Makefile with 10 common development commands
  - Set up pre-commit hooks with ruff linter and mypy type checker
  - Configure GitHub Actions CI: lint, type-check, test matrix across 6 services
  - All Dockerfiles verified and optimized

  Closes #1"
- git push origin feature/001-project-scaffold
- gh pr create --title "feat(infra): project scaffold, Docker Compose, CI/CD" --body "Implements #1. Full project infrastructure scaffold." --base main
- gh pr merge --squash --auto
- gh issue close 1
```

---

## Issue #2: Database schema, migrations, and seed data

```
Implement GitHub Issue #2: Database schema, migrations, and seed data.

Context: The SQL init script exists at infrastructure/docker/postgres/init.sql with the complete schema. Now implement Alembic migrations and SQLAlchemy ORM models.

Tasks:
1. Set up Alembic in services/gateway-service/ with alembic.ini and migrations directory
2. Create SQLAlchemy ORM models in shared/models/orm.py mapping all tables from init.sql:
   - Users, RegulatorySource, RegulatoryDocument, DocumentEnrichment, DocumentEmbedding, ComplianceReport, WatchRule, NotificationLog, AuditLog
   - Use mapped_column, proper relationships, and type annotations
3. Create the initial Alembic migration that matches the init.sql schema
4. Create scripts/seed_data.py that inserts:
   - Admin user (email: admin@regulatorai.com, password: hashed bcrypt of "admin123")
   - 4 regulatory sources (EU AI Act, US Federal Register, UK ICO, NIST)
   - 3 sample regulatory documents with realistic content
5. Add database session management (async session factory) in shared/utils/database.py
6. Write tests: test ORM model creation, test seed script, test db session lifecycle

After implementation:
- git checkout -b feature/002-database-schema
- git add -A
- git commit -m "feat(db): implement database schema with Alembic migrations and seed data

  - Create SQLAlchemy ORM models for all 9 tables with relationships
  - Configure Alembic with async PostgreSQL driver
  - Add initial migration matching complete schema (pgvector, UUID, JSONB)
  - Implement seed script with admin user and 4 regulatory sources
  - Add async database session factory with connection pooling
  - Write comprehensive tests for ORM models and database lifecycle
  - Add HNSW index on vector embedding column for ANN search

  Closes #2"
- git push origin feature/002-database-schema
- gh pr create --title "feat(db): database schema, migrations, seed data" --body "Implements #2. Complete PostgreSQL schema with pgvector support." --base main
- gh pr merge --squash --auto
- gh issue close 2
```

---

## Issue #3: Shared library — Pydantic models, config, utilities

```
Implement GitHub Issue #3: Shared library with Pydantic models, config, and utilities.

Context: shared/models/schemas.py and shared/config/settings.py already exist with base implementations. Enhance and complete them.

Tasks:
1. Review and enhance shared/models/schemas.py — ensure all models have proper validators, examples, and JSON schema config
2. Create shared/utils/security.py:
   - password_hash(password) -> str (bcrypt)
   - password_verify(password, hash) -> bool
   - create_access_token(user_id, role, expires_delta) -> str (JWT)
   - create_refresh_token(user_id) -> str (JWT)
   - decode_token(token) -> dict
   - generate_content_hash(content) -> str (SHA-256)
3. Create shared/utils/pagination.py:
   - PaginationParams(page, page_size) with validation
   - paginate_query(query, params) -> PaginatedResponse
4. Create shared/utils/events.py:
   - RedisEventPublisher: publish(channel, event: DocumentEvent)
   - RedisEventSubscriber: subscribe(channel, callback)
5. Create shared/utils/logging.py:
   - configure_logging(service_name, level) with structlog JSON processor
   - RequestIdMiddleware for FastAPI
6. Ensure 100% test coverage: shared/models/test_schemas.py + tests for each utility module
7. Create shared/utils/test_security.py, test_pagination.py, test_events.py

After implementation:
- git checkout -b feature/003-shared-library
- git add -A
- git commit -m "feat(shared): implement shared library with models, config, and utilities

  - Enhance Pydantic v2 models with validators and JSON schema examples
  - Add security utilities: bcrypt hashing, JWT encode/decode, SHA-256 content hash
  - Add pagination helpers with validated params and response wrapper
  - Add Redis Pub/Sub event publisher and subscriber for inter-service messaging
  - Add structured logging with structlog and request ID propagation middleware
  - Achieve 100% test coverage across all shared modules
  - All utilities use async-first patterns where applicable

  Closes #3"
- git push origin feature/003-shared-library
- gh pr create --title "feat(shared): Pydantic models, config, security, event utilities" --body "Implements #3. Complete shared library for all services." --base main
- gh pr merge --squash --auto
- gh issue close 3
```

---

## Issue #4: Gateway Service — Auth, routing, rate limiting

```
Implement GitHub Issue #4: Gateway Service with full authentication, routing, and rate limiting.

Context: services/gateway-service/src/main.py exists with route stubs. Route files exist as stubs in src/routes/.

Tasks:
1. Implement src/routes/auth.py fully:
   - POST /login: validate credentials against DB, return JWT pair
   - POST /register: create user with hashed password, return user
   - POST /refresh: validate refresh token, issue new pair
   - POST /logout: blacklist token in Redis
2. Create src/middleware/auth.py:
   - get_current_user dependency (decode JWT, fetch user from DB)
   - require_role(roles: list) dependency factory
3. Implement src/routes/documents.py: proxy to ingestion/agent services via httpx
4. Implement src/routes/search.py: proxy to search service
5. Implement src/routes/reports.py: proxy to compliance service
6. Implement src/routes/users.py: CRUD for user management (admin only)
7. Add rate limiting: 100/min general, 10/min auth endpoints, 30/min LLM-heavy
8. Add request logging middleware with structlog
9. Add health check that pings all downstream services
10. Write comprehensive tests: test_auth.py, test_documents.py, test_middleware.py

After implementation:
- git checkout -b feature/004-gateway-service
- git add -A
- git commit -m "feat(gateway): implement API Gateway with JWT auth, RBAC, and rate limiting

  - Implement full JWT authentication flow (login, register, refresh, logout)
  - Add bcrypt password hashing and Redis token blacklist
  - Create role-based access control middleware (admin, analyst, viewer)
  - Implement service proxy routes via httpx async client
  - Configure rate limiting: 100/min general, 10/min auth, 30/min LLM routes
  - Add structured request/response logging with correlation IDs
  - Add aggregated health check endpoint for all downstream services
  - Write 15+ unit and integration tests for auth, middleware, and routing

  Closes #4"
- git push origin feature/004-gateway-service
- gh pr create --title "feat(gateway): JWT auth, RBAC, rate limiting, service routing" --body "Implements #4. Production-grade API Gateway." --base main
- gh pr merge --squash --auto
- gh issue close 4
```

---

## Issue #5: Monitoring stack

```
Implement GitHub Issue #5: Monitoring stack with Prometheus, Grafana dashboards, and structured logging.

Tasks:
1. Enhance infrastructure/docker/prometheus/prometheus.yml with proper relabel configs and scrape intervals
2. Create infrastructure/docker/grafana/provisioning/dashboards/service-health.json — Grafana dashboard JSON:
   - Panel: Service status (up/down) for all 6 services
   - Panel: Request rate per service (time series)
   - Panel: Latency percentiles (p50, p95, p99) per service
   - Panel: Error rate per service
3. Create infrastructure/docker/grafana/provisioning/dashboards/agent-pipeline.json:
   - Panel: Documents processed per hour
   - Panel: Average processing time per agent node
   - Panel: Token usage per document (bar chart)
   - Panel: Cost tracking (cumulative line chart)
4. Create infrastructure/docker/grafana/provisioning/datasources/prometheus.yml — auto-provision Prometheus datasource
5. Add Prometheus instrumentation to each service's main.py using prometheus_client
6. Create alerting rules in infrastructure/docker/prometheus/alerts.yml

After implementation:
- git checkout -b feature/005-monitoring-stack
- git add -A
- git commit -m "feat(infra): implement monitoring stack with Prometheus and Grafana

  - Configure Prometheus scraping for all 6 backend services
  - Create service health Grafana dashboard with status, latency, and error panels
  - Create agent pipeline dashboard with processing metrics and cost tracking
  - Auto-provision Prometheus datasource in Grafana
  - Add prometheus_client instrumentation to all service endpoints
  - Define alerting rules: service down, high error rate, latency degradation
  - Add structured JSON logging with request ID correlation across services

  Closes #5"
- git push origin feature/005-monitoring-stack
- gh pr create --title "feat(infra): Prometheus, Grafana dashboards, alerting" --body "Implements #5. Full observability stack." --base main
- gh pr merge --squash --auto
- gh issue close 5
```

---

## Issue #6: Ingestion Service

```
Implement GitHub Issue #6: Ingestion Service with crawlers, parsers, and Celery tasks.

Context: services/ingestion-service/src/main.py exists as a stub.

Tasks:
1. Implement src/main.py with full FastAPI app:
   - GET /health
   - GET /api/v1/sources — list regulatory sources
   - POST /api/v1/sources — add new source
   - POST /api/v1/sources/{id}/crawl — trigger manual crawl
   - POST /api/v1/upload — upload document manually
   - GET /api/v1/ingestion/stats — ingestion statistics
2. Create src/crawlers/rss_crawler.py — feedparser-based RSS/Atom crawler
3. Create src/crawlers/web_crawler.py — httpx + BeautifulSoup HTML crawler
4. Create src/parsers/pdf_parser.py — PyMuPDF text extraction
5. Create src/parsers/html_parser.py — BeautifulSoup content extraction
6. Create src/parsers/normalizer.py — normalize all content into RegulatoryDocument schema
7. Create src/tasks.py — Celery tasks:
   - ingest_source(source_id): crawl and ingest a single source
   - ingest_all_sources(): crawl all active sources
   - Celery beat schedule based on source.crawl_frequency_minutes
8. Implement deduplication via SHA-256 content hash
9. Publish `document.ingested` event to Redis on successful ingestion
10. Add prometheus metrics: docs_ingested_total, ingestion_duration, errors
11. Write tests: test_rss_crawler.py, test_parsers.py, test_normalizer.py, test_tasks.py

After implementation:
- git checkout -b feature/006-ingestion-service
- git add -A
- git commit -m "feat(ingestion): implement document ingestion with crawlers and Celery

  - Create RSS/Atom feed crawler using feedparser
  - Create web crawler using httpx and BeautifulSoup
  - Implement PDF text extraction with PyMuPDF
  - Implement HTML content extraction and cleaning
  - Create content normalizer producing unified RegulatoryDocument schema
  - Set up Celery tasks for async ingestion with configurable scheduling
  - Add SHA-256 deduplication to prevent duplicate document storage
  - Publish document.ingested events to Redis Pub/Sub
  - Add Prometheus metrics: ingestion rate, duration, error tracking
  - Write 12+ tests covering crawlers, parsers, and task execution

  Closes #6"
- git push origin feature/006-ingestion-service
- gh pr create --title "feat(ingestion): crawlers, parsers, Celery async pipeline" --body "Implements #6. Complete document ingestion service." --base main
- gh pr merge --squash --auto
- gh issue close 6
```

---

## Issue #7: Agent Service — LangGraph pipeline

```
Implement GitHub Issue #7: Agent Service with full LangGraph multi-agent pipeline.

Context: services/agent-service/src/pipeline.py exists with node stubs and prompt templates.

Tasks:
1. Install and configure LangGraph and LangChain OpenAI
2. Fully implement each node in src/pipeline.py:
   - router_node: inspect metadata, detect language, set processing flags
   - summarizer_node: call OpenAI with SUMMARIZER_PROMPT, parse structured JSON output
   - classifier_node: multi-label classification with confidence scores
   - impact_ranker_node: generate region x product scoring matrix
   - drafter_node: generate compliance response for configurable audience
   - aggregator_node: merge all outputs, validate, calculate confidence, persist to DB
3. Build the LangGraph StateGraph in build_agent_graph():
   - Wire all nodes with correct edges
   - Add conditional routing (skip drafter for low-impact docs)
   - Add error handling edges (route to error handler on failure)
4. Create src/llm_client.py:
   - OpenAI client wrapper with retry logic (exponential backoff)
   - Token counting with tiktoken
   - Cost calculation per model
   - Rate limiting awareness
5. Create src/chunker.py:
   - Split long documents into overlapping chunks
   - Respect token limits (8k default)
6. Create src/event_handler.py:
   - Subscribe to `document.ingested` events from Redis
   - Trigger pipeline execution
   - Publish `document.enriched` or `document.failed` events
7. Update src/main.py with full API endpoints
8. Write tests with MOCKED LLM responses (do not call real OpenAI):
   - test_pipeline.py: test each node with fixture data
   - test_llm_client.py: test retry logic, token counting
   - test_chunker.py: test document splitting
   - test_event_handler.py: test event processing

After implementation:
- git checkout -b feature/007-agent-service
- git add -A
- git commit -m "feat(agents): implement LangGraph multi-agent pipeline with 5 AI agents

  - Build LangGraph StateGraph with Router, Summarizer, Classifier, Impact Ranker, Drafter, and Aggregator nodes
  - Implement structured output parsing for all LLM responses (JSON mode)
  - Add conditional routing: skip drafter for low-impact documents
  - Create OpenAI client wrapper with exponential backoff retry and rate limiting
  - Implement token counting with tiktoken and cost tracking per document
  - Add document chunker for handling documents exceeding context window
  - Subscribe to document.ingested Redis events to trigger pipeline
  - Publish document.enriched events on completion for downstream services
  - Persist enrichment results to PostgreSQL via async SQLAlchemy
  - Write 18+ tests with mocked LLM responses covering all nodes and utilities

  Closes #7"
- git push origin feature/007-agent-service
- gh pr create --title "feat(agents): LangGraph multi-agent pipeline with 5 AI agents" --body "Implements #7. Core AI analysis engine." --base main
- gh pr merge --squash --auto
- gh issue close 7
```

---

## Issue #8: Search Service

```
Implement GitHub Issue #8: Search Service with Elasticsearch and pgvector hybrid search.

Tasks:
1. Create src/main.py with endpoints:
   - POST /api/v1/search — hybrid search
   - GET /api/v1/search/suggest?q= — autocomplete
   - GET /api/v1/search/facets — available facets
   - POST /api/v1/index/{document_id} — index a document
2. Create src/elasticsearch_client.py:
   - Index mapping for regulatory documents (title, content, metadata fields)
   - BM25 search with highlighting
   - Completion suggester for autocomplete
   - Faceted aggregations
3. Create src/vector_search.py:
   - Generate embeddings via OpenAI text-embedding-3-small
   - Store in pgvector
   - Cosine similarity search
4. Create src/hybrid_search.py:
   - Reciprocal Rank Fusion (RRF) implementation
   - Configurable weights between keyword and semantic
   - Merge and deduplicate results
5. Create src/indexer.py:
   - Listen for `document.enriched` events
   - Index document in Elasticsearch
   - Generate and store embeddings in pgvector
6. Write tests: test_es_client.py, test_vector_search.py, test_hybrid.py, test_rrf.py

After implementation:
- git checkout -b feature/008-search-service
- git add -A
- git commit -m "feat(search): implement hybrid search with Elasticsearch and pgvector

  - Create Elasticsearch index mapping with BM25 scoring and highlighting
  - Implement semantic search using OpenAI embeddings and pgvector cosine similarity
  - Build Reciprocal Rank Fusion (RRF) for hybrid result merging
  - Add faceted filtering: jurisdiction, category, date range, urgency level
  - Implement autocomplete using Elasticsearch completion suggester
  - Create event-driven indexer subscribing to document.enriched events
  - Support configurable search weights between keyword and semantic modes
  - Write 14+ tests covering search strategies, RRF, and indexing

  Closes #8"
- git push origin feature/008-search-service
- gh pr create --title "feat(search): Elasticsearch + pgvector hybrid search" --body "Implements #8. Dual search with RRF merging." --base main
- gh pr merge --squash --auto
- gh issue close 8
```

---

## Issue #9: Compliance Service

```
Implement GitHub Issue #9: Compliance Service with report generation.

Tasks:
1. Implement src/main.py with endpoints:
   - POST /api/v1/reports — create report
   - GET /api/v1/reports — list reports
   - GET /api/v1/reports/{id} — get report
   - GET /api/v1/reports/{id}/download?format=pdf — download
   - GET /api/v1/templates — list available templates
2. Create src/templates/ directory with Jinja2 templates:
   - standard_compliance.html — full compliance report
   - executive_summary.html — board-level summary
   - detailed_analysis.html — deep-dive with all enrichment data
3. Create src/generator.py:
   - render_report(template_id, documents, enrichments) -> HTML
   - html_to_pdf(html) using WeasyPrint
   - html_to_docx(html) using python-docx
4. Create src/storage.py: file storage abstraction (local dev, S3 prod)
5. Write tests for template rendering, PDF generation, DOCX generation

After implementation:
- git checkout -b feature/009-compliance-service
- git add -A
- git commit -m "feat(compliance): implement report generation with PDF and DOCX output

  - Create 3 Jinja2 report templates: standard, executive summary, detailed analysis
  - Implement PDF generation using WeasyPrint with professional styling
  - Implement DOCX generation using python-docx with formatted tables and sections
  - Add file storage abstraction supporting local filesystem and S3
  - Create report versioning and status tracking (draft -> generating -> completed)
  - Support batch reports aggregating multiple regulatory documents
  - Write 10+ tests covering template rendering and document generation

  Closes #9"
- git push origin feature/009-compliance-service
- gh pr create --title "feat(compliance): report generation with PDF/DOCX" --body "Implements #9. Compliance report engine." --base main
- gh pr merge --squash --auto
- gh issue close 9
```

---

## Issue #10: Notification Service

```
Implement GitHub Issue #10: Notification Service with watch rules and multi-channel delivery.

Tasks:
1. Implement src/main.py with endpoints:
   - CRUD for watch rules
   - GET /api/v1/notifications — notification history
   - PUT /api/v1/notifications/{id}/read — mark as read
   - GET /api/v1/notifications/preferences — user preferences
2. Create src/rule_engine.py: evaluate watch rule conditions against document enrichments
3. Create src/channels/email.py: async email sending via aiosmtplib
4. Create src/channels/slack.py: Slack webhook delivery
5. Create src/channels/inapp.py: in-app notification storage
6. Create src/event_handler.py: subscribe to document.enriched, match rules, dispatch
7. Create src/templates/: email HTML templates, Slack block templates
8. Write tests for rule matching, email rendering, event handling

After implementation:
- git checkout -b feature/010-notification-service
- git add -A
- git commit -m "feat(notifications): implement watch rules engine and multi-channel delivery

  - Create watch rule CRUD API with condition builder
  - Implement rule matching engine evaluating conditions against enriched documents
  - Add async email delivery via aiosmtplib with HTML templates
  - Add Slack webhook integration with Block Kit formatting
  - Add in-app notification storage with read tracking
  - Subscribe to document.enriched events for real-time rule evaluation
  - Implement per-user rate limiting to prevent notification spam
  - Write 12+ tests for rule matching, channel delivery, and event handling

  Closes #10"
- git push origin feature/010-notification-service
- gh pr create --title "feat(notifications): watch rules, email, Slack, in-app alerts" --body "Implements #10. Event-driven notification system." --base main
- gh pr merge --squash --auto
- gh issue close 10
```

---

## Issue #11: Frontend scaffold

```
Implement GitHub Issue #11: Frontend scaffold with React 18, TypeScript, TailwindCSS.

Tasks:
1. Initialize Vite + React 18 + TypeScript in frontend/
2. Install and configure:
   - TailwindCSS with custom theme (deep navy #0F172A base, amber #F59E0B accent, slate grays)
   - React Router v6
   - TanStack Query
   - Zustand for auth store
   - Axios with JWT interceptor
   - Lucide React icons
   - Recharts
3. Create the layout structure:
   - src/components/layout/Sidebar.tsx — collapsible nav with icons
   - src/components/layout/Header.tsx — search bar, user avatar, notifications bell
   - src/components/layout/MainLayout.tsx — sidebar + header + content wrapper
4. Create src/services/api.ts — Axios instance with base URL, JWT interceptor, refresh logic
5. Create src/store/authStore.ts — Zustand store for auth state
6. Create src/styles/globals.css with Tailwind directives and custom styles
7. Set up routing in src/App.tsx: /, /login, /documents, /search, /reports, /settings
8. Create src/components/ui/ primitives: Button, Card, Badge, Input, Select, Modal, Toast
9. Create Dockerfile: multi-stage build (node build -> nginx serve)
10. Ensure dark/light theme with CSS variables

Design direction: Enterprise legal-tech aesthetic. Deep navy/charcoal backgrounds, amber/gold accents for CTAs and highlights, crisp DM Sans or Instrument Sans typography, generous whitespace, glass morphism cards with subtle borders. Professional data density, NOT playful or consumer-app vibes.

After implementation:
- git checkout -b feature/011-frontend-scaffold
- git add -A
- git commit -m "feat(frontend): scaffold React 18 + TypeScript + TailwindCSS enterprise UI

  - Initialize Vite project with React 18 and TypeScript strict mode
  - Configure TailwindCSS with enterprise design system (navy/amber/slate palette)
  - Create responsive layout: collapsible sidebar, header with search and notifications
  - Set up React Router v6 with protected route wrapper
  - Configure TanStack Query for server state management
  - Create Zustand auth store with JWT token lifecycle
  - Build Axios API client with automatic token refresh interceptor
  - Create 8 reusable UI primitives: Button, Card, Badge, Input, Select, Modal, Toast, Spinner
  - Implement dark/light theme toggle with CSS custom properties
  - Add multi-stage Dockerfile (node build -> nginx production serve)

  Closes #11"
- git push origin feature/011-frontend-scaffold
- gh pr create --title "feat(frontend): React 18 + TS + Tailwind enterprise scaffold" --body "Implements #11. Frontend foundation with design system." --base main
- gh pr merge --squash --auto
- gh issue close 11
```

---

## Issue #12: Auth pages

```
Implement GitHub Issue #12: Authentication pages — login, register, forgot password.

Tasks:
1. Create src/pages/Login.tsx:
   - Clean enterprise login form with email + password
   - Form validation with react-hook-form + zod
   - Error states, loading states
   - "Remember me" checkbox
   - Link to register and forgot password
   - Dark background with centered card, subtle gradient
2. Create src/pages/Register.tsx:
   - Email, password, confirm password, full name, organization, role select
   - Password strength indicator
3. Create src/pages/ForgotPassword.tsx: email input, success message
4. Create src/hooks/useAuth.ts: login, register, logout mutations with TanStack Query
5. Create src/components/auth/ProtectedRoute.tsx: redirect to /login if not authenticated
6. Update routing to use ProtectedRoute wrapper
7. Write tests: form validation, auth flow, protected route

After implementation:
- git checkout -b feature/012-auth-pages
- git add -A
- git commit -m "feat(frontend): implement authentication pages with form validation

  - Create login page with email/password form and remember-me option
  - Create registration page with password strength indicator and role selection
  - Create forgot password flow with email submission
  - Implement form validation using react-hook-form and zod schemas
  - Add useAuth hook with TanStack Query mutations for all auth operations
  - Create ProtectedRoute component with automatic redirect to login
  - Style with enterprise aesthetic: dark gradient background, glass card
  - Write tests for form validation, auth state management, and route protection

  Closes #12"
- git push origin feature/012-auth-pages
- gh pr create --title "feat(frontend): auth pages with form validation" --body "Implements #12. Login, register, forgot password." --base main
- gh pr merge --squash --auto
- gh issue close 12
```

---

## Issue #13: Dashboard page

```
Implement GitHub Issue #13: Main dashboard with KPIs, charts, risk heatmap.

Tasks:
1. Create src/pages/Dashboard.tsx with grid layout:
   - Top row: 4 KPI cards (total docs, pending reviews, high-urgency, reports generated)
   - Middle row: Activity timeline (Recharts AreaChart, 30 days) + Jurisdiction risk heatmap
   - Bottom row: Recent documents feed (table with status badges)
2. Create src/components/dashboard/KPICard.tsx — animated counter, trend arrow, icon
3. Create src/components/dashboard/ActivityChart.tsx — Recharts area chart with gradient fill
4. Create src/components/dashboard/RiskHeatmap.tsx — grid visualization of region x impact scores using color intensity
5. Create src/components/dashboard/RecentDocuments.tsx — table with urgency badges, jurisdiction flags, time ago
6. Create src/hooks/useDashboard.ts — TanStack Query hooks for dashboard data
7. Add skeleton loading states for each widget
8. Add auto-refresh toggle (30s, 60s, off)

After implementation:
- git checkout -b feature/013-dashboard-page
- git add -A
- git commit -m "feat(frontend): implement enterprise dashboard with KPIs and risk heatmap

  - Create responsive grid dashboard with 4 KPI cards and animated counters
  - Build 30-day regulatory activity timeline using Recharts area chart
  - Implement jurisdiction risk heatmap with color-intensity scoring grid
  - Create recent documents feed with urgency badges and status indicators
  - Add skeleton loading states for all dashboard widgets
  - Implement auto-refresh with configurable intervals (30s, 60s, off)
  - Style with enterprise dark theme, amber accent data visualizations

  Closes #13"
- git push origin feature/013-dashboard-page
- gh pr create --title "feat(frontend): enterprise dashboard with KPIs and heatmap" --body "Implements #13. Main dashboard page." --base main
- gh pr merge --squash --auto
- gh issue close 13
```

---

## Issue #14: Document explorer

```
Implement GitHub Issue #14: Document explorer with list, detail view, and enrichment display.

Tasks:
1. Create src/pages/Documents.tsx — main list page with filter sidebar
2. Create src/pages/DocumentDetail.tsx — full document view with enrichment tabs
3. Create src/components/documents/DocumentTable.tsx — sortable table with selection
4. Create src/components/documents/DocumentCard.tsx — card view alternative
5. Create src/components/documents/FilterSidebar.tsx — jurisdiction, category, status, urgency, date range filters
6. Create src/components/documents/EnrichmentPanel.tsx:
   - Summary tab with formatted text
   - Key Changes tab with collapsible items
   - Classification tab with confidence progress bars
   - Impact Matrix tab with color-coded grid
   - Draft Response tab with copy button
7. Create src/components/documents/StatusBadge.tsx — colored badges for document status
8. Add view toggle (table/card), URL-based filter state, bulk selection

After implementation:
- git checkout -b feature/014-document-explorer
- git add -A
- git commit -m "feat(frontend): implement document explorer with enrichment display

  - Create document list page with table and card view toggle
  - Build filter sidebar: jurisdiction, category, status, urgency, date range
  - Implement document detail page with tabbed enrichment display
  - Create summary, key changes, classification, impact matrix, and draft tabs
  - Add confidence progress bars for classification labels
  - Build color-coded impact scoring matrix visualization
  - Implement URL-based filter state for shareable views
  - Add bulk document selection for batch operations

  Closes #14"
- git push origin feature/014-document-explorer
- gh pr create --title "feat(frontend): document explorer with AI enrichment display" --body "Implements #14. Document browser and detail view." --base main
- gh pr merge --squash --auto
- gh issue close 14
```

---

## Issue #15: Search page

```
Implement GitHub Issue #15: Search page with facets and rich results.

Tasks:
1. Create src/pages/Search.tsx — search input + facets + results
2. Create src/components/search/SearchInput.tsx — with autocomplete dropdown, search type toggle
3. Create src/components/search/FacetPanel.tsx — checkbox facets with counts
4. Create src/components/search/ResultCard.tsx — title, highlighted snippet, metadata badges, score
5. Create src/components/search/SearchHistory.tsx — recent searches list
6. Add keyboard shortcut: Cmd+K to focus search globally
7. URL-based search state (?q=&jurisdiction=&type=)
8. Empty states and no-results with suggestions

After implementation:
- git checkout -b feature/015-search-page
- git add -A
- git commit -m "feat(frontend): implement search page with autocomplete and faceted filtering

  - Create search page with autocomplete input and search type toggle (keyword/semantic/hybrid)
  - Build faceted filter panel with checkbox options and result counts
  - Implement result cards with highlighted snippet text and metadata badges
  - Add search history tracking with recent queries list
  - Implement Cmd+K global keyboard shortcut to focus search
  - Create URL-based search state for bookmarkable and shareable searches
  - Add empty state and no-results messaging with query suggestions

  Closes #15"
- git push origin feature/015-search-page
- gh pr create --title "feat(frontend): search with autocomplete, facets, highlights" --body "Implements #15. Full search experience." --base main
- gh pr merge --squash --auto
- gh issue close 15
```

---

## Issue #16: Reports page

```
Implement GitHub Issue #16: Reports management page.

Tasks:
1. Create src/pages/Reports.tsx — report list with filters
2. Create src/components/reports/ReportWizard.tsx — multi-step creation:
   Step 1: Select documents (searchable multi-select)
   Step 2: Choose template (card selection)
   Step 3: Configure options (title, audience, format)
   Step 4: Review and generate
3. Create src/components/reports/ReportCard.tsx — status, date, actions
4. Create src/components/reports/ReportPreview.tsx — in-browser PDF/HTML preview
5. Add download buttons for PDF and DOCX formats

After implementation:
- git checkout -b feature/016-reports-page
- git add -A
- git commit -m "feat(frontend): implement reports page with creation wizard and preview

  - Create report list page with status, type, and date filters
  - Build 4-step report creation wizard: select docs, choose template, configure, review
  - Implement searchable multi-select for document selection
  - Add in-browser report preview component
  - Create download buttons for PDF and DOCX formats
  - Add report status tracking with visual indicators

  Closes #16"
- git push origin feature/016-reports-page
- gh pr create --title "feat(frontend): reports page with creation wizard" --body "Implements #16. Compliance report management UI." --base main
- gh pr merge --squash --auto
- gh issue close 16
```

---

## Issue #17: Settings page

```
Implement GitHub Issue #17: Settings page with profile, watch rules, and admin panel.

Tasks:
1. Create src/pages/Settings.tsx — tabbed settings interface
2. Create src/components/settings/ProfileSection.tsx — name, email, org, password change
3. Create src/components/settings/WatchRulesSection.tsx:
   - Rule list with active/inactive toggle
   - Create rule form with visual condition builder
   - Condition builder: field select, operator select, value input
   - Channel selection (email, slack, in-app checkboxes)
4. Create src/components/settings/NotificationPreferences.tsx — channel toggles, digest frequency
5. Create src/components/settings/AdminPanel.tsx (admin only):
   - User management table with invite/deactivate
   - Regulatory source management with add/edit/toggle
   - System health summary

After implementation:
- git checkout -b feature/017-settings-page
- git add -A
- git commit -m "feat(frontend): implement settings page with watch rules and admin panel

  - Create tabbed settings interface: Profile, Watch Rules, Notifications, Admin
  - Build profile section with password change and organization details
  - Implement visual watch rule condition builder with drag-and-drop
  - Add notification preference controls for channel and digest frequency
  - Create admin panel with user management and source configuration
  - Implement role-based visibility (admin panel hidden for non-admins)

  Closes #17"
- git push origin feature/017-settings-page
- gh pr create --title "feat(frontend): settings, watch rules, admin panel" --body "Implements #17. User settings and administration." --base main
- gh pr merge --squash --auto
- gh issue close 17
```

---

## Issue #18: E2E tests, load tests, security audit

```
Implement GitHub Issue #18: Comprehensive testing suite.

Tasks:
1. Set up Playwright in frontend/:
   - tests/e2e/auth.spec.ts — login flow, register, logout
   - tests/e2e/search.spec.ts — search, filter, view results
   - tests/e2e/documents.spec.ts — browse, view detail, check enrichment
   - tests/e2e/reports.spec.ts — create report wizard flow
2. Create scripts/load_test.py using Locust:
   - UserSearchScenario: concurrent search requests
   - IngestionScenario: concurrent document uploads
   - MixedScenario: realistic user behavior mix
3. Create security tests:
   - test_sql_injection.py — parameterized query verification
   - test_xss.py — HTML sanitization in stored content
   - test_rbac.py — endpoint access by role matrix
   - test_rate_limiting.py — verify limits are enforced
4. Create test data factories using factory_boy
5. Update docker-compose.test.yml with all test dependencies
6. Achieve 80%+ backend coverage, 70%+ frontend coverage

After implementation:
- git checkout -b feature/018-testing-suite
- git add -A
- git commit -m "feat(testing): implement E2E, load, and security testing suite

  - Create Playwright E2E tests for auth, search, documents, and reports flows
  - Build Locust load test scenarios for search and ingestion throughput
  - Add security tests: SQL injection, XSS, RBAC verification, rate limiting
  - Create test data factories with factory_boy for realistic test data
  - Configure test Docker Compose with ephemeral services
  - Achieve 80%+ backend and 70%+ frontend test coverage

  Closes #18"
- git push origin feature/018-testing-suite
- gh pr create --title "feat(testing): E2E, load tests, security audit" --body "Implements #18. Comprehensive test coverage." --base main
- gh pr merge --squash --auto
- gh issue close 18
```

---

## Issue #19: Production deployment

```
Implement GitHub Issue #19: Kubernetes Helm charts and Terraform modules.

Tasks:
1. Create infrastructure/kubernetes/helm/regulatorai/:
   - Chart.yaml, values.yaml, values-prod.yaml
   - templates/ for each service: deployment, service, hpa, configmap
   - Ingress with TLS termination
   - PVCs for databases
2. Create infrastructure/terraform/:
   - main.tf — provider config
   - vpc.tf — VPC and subnets
   - eks.tf — EKS cluster (or GKE)
   - rds.tf — managed PostgreSQL with pgvector
   - elasticache.tf — managed Redis
   - elasticsearch.tf — managed Elasticsearch
   - outputs.tf — cluster endpoint, service URLs
   - variables.tf and prod.tfvars
3. Create infrastructure/docker/caddy/Caddyfile for production reverse proxy
4. Create database backup CronJob manifest
5. Document zero-downtime rolling update strategy

After implementation:
- git checkout -b feature/019-production-deployment
- git add -A
- git commit -m "feat(infra): implement Kubernetes Helm charts and Terraform IaC

  - Create Helm chart with templates for all services, HPA, and Ingress
  - Add production values with resource limits, replicas, and TLS config
  - Create Terraform modules: VPC, EKS, RDS (pgvector), ElastiCache, managed ES
  - Configure Caddy reverse proxy with automatic TLS for production Docker Compose
  - Add database backup CronJob with retention policy
  - Document zero-downtime rolling update strategy

  Closes #19"
- git push origin feature/019-production-deployment
- gh pr create --title "feat(infra): Kubernetes Helm + Terraform production deployment" --body "Implements #19. Production-ready infrastructure." --base main
- gh pr merge --squash --auto
- gh issue close 19
```

---

## Issue #20: Documentation

```
Implement GitHub Issue #20: Complete project documentation.

Tasks:
1. Ensure docs/architecture/ has all C4 diagrams, sequence diagrams, and ADRs
2. Create docs/user-guide.md: getting started walkthrough for end users
3. Create docs/api-reference.md: link to auto-generated OpenAPI docs with examples
4. Create CONTRIBUTING.md: setup guide, coding standards, PR process, commit conventions
5. Create CHANGELOG.md with v0.1.0 entries
6. Create docs/troubleshooting.md: common issues and solutions
7. Create docs/runbook.md: operational procedures (restart service, clear cache, reindex, backup/restore)
8. Update README.md with final project state

After implementation:
- git checkout -b feature/020-documentation
- git add -A
- git commit -m "docs: complete project documentation with guides and runbook

  - Finalize C4 architecture diagrams (context, container, component)
  - Add sequence diagrams for all major flows
  - Create user guide with feature walkthroughs
  - Create API reference with example requests and responses
  - Write CONTRIBUTING.md with coding standards and PR process
  - Create CHANGELOG.md for v0.1.0
  - Add troubleshooting guide for common issues
  - Create operational runbook for production management

  Closes #20"
- git push origin feature/020-documentation
- gh pr create --title "docs: complete project documentation" --body "Implements #20. Full documentation suite." --base main
- gh pr merge --squash --auto
- gh issue close 20
```

---

## Completion Checklist

After running all 20 prompts, verify:

- [ ] All 20 GitHub issues are closed
- [ ] All 20 PRs are merged to main
- [ ] `docker compose up` starts all services successfully
- [ ] `http://localhost:3000` shows the enterprise dashboard
- [ ] `http://localhost:8000/docs` shows the API documentation
- [ ] All tests pass: `make test`
- [ ] No lint errors: `make lint`
