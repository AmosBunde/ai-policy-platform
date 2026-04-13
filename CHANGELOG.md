# Changelog

All notable changes to RegulatorAI are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-04-13

### Added

#### Backend Services
- Gateway Service: JWT authentication, RBAC (viewer/analyst/admin), rate limiting, request routing
- Ingestion Service: RSS/API/crawler document ingestion, content normalization, deduplication
- Agent Service: LangGraph multi-agent pipeline (summarizer, classifier, impact ranker, drafter)
- Compliance Service: Report generation (PDF/DOCX), template management
- Search Service: Hybrid search (Elasticsearch BM25 + pgvector semantic) with Reciprocal Rank Fusion
- Notification Service: Watch rules engine, multi-channel delivery (email, Slack, in-app)

#### Frontend
- React 18 + TypeScript + TailwindCSS enterprise dashboard
- Authentication pages (login, register, forgot password) with security-aware UX
- Dashboard with KPIs, activity charts, risk heatmap, recent documents
- Document explorer with enrichment display (summary, key changes, classification, impact, draft)
- Reports page with 4-step creation wizard (select docs, template, configure, generate)
- Settings with tabbed layout: profile, watch rules, notifications, admin panel
- Search page with autocomplete, facets, and safe highlighting

#### Security
- SQL injection prevention: parameterized queries, UUID validation on all path parameters
- XSS prevention: Pydantic field validators with HTML sanitization, CSP headers
- RBAC enforcement: admin panel hidden (not rendered) for non-admin users
- JWT security: HS256-only (algorithm confusion prevented), token revocation via Redis blacklist
- SSRF prevention: URL scheme validation (http/https only), private subnet data stores
- Path traversal prevention: UUID validation, read-only pod filesystems
- Rate limiting on auth endpoints, security headers (HSTS, X-Frame-Options, CSP)
- Pod security contexts: non-root, read-only filesystem, dropped capabilities

#### Infrastructure
- Docker Compose setup (development, production, test configurations)
- Kubernetes Helm chart with HPA, NetworkPolicy, Ingress with TLS
- Terraform IaC: VPC, EKS, RDS (encrypted), ElastiCache (encrypted), OpenSearch (encrypted)
- CloudTrail and VPC flow logs for audit trail
- Database backup CronJob: daily pg_dump to S3 with AES-256 encryption, 30-day retention
- Caddy reverse proxy with automatic TLS, HSTS, rate limiting

#### Testing
- 160 backend tests (47 unit + 113 security tests) — all passing
- 76 frontend unit tests — all passing
- Playwright E2E test suite: auth, search, documents, reports
- Locust load testing: 100 concurrent users, mixed behavior profiles
- Security test coverage: SQLi, XSS, RBAC, JWT tampering, SSRF, path traversal, rate limiting

#### Monitoring
- Prometheus metrics collection across all services
- Grafana dashboards: service health, agent pipeline, security monitoring
- Alert rules: service down, high error rate, brute force detection, rate limit hits

#### Documentation
- C4 architecture diagrams (context, container, component)
- Sequence diagrams for 5 critical flows
- 7 Architecture Decision Records (ADRs)
- User guide, API reference, security documentation
- Operational runbook with incident response procedures
- Contributing guidelines with security awareness
