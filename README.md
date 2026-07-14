# RegulatorAI — AI Policy Research & Compliance Automation Platform

> Enterprise-grade system using AI agents to monitor, analyze, and summarize global AI regulations and generate compliance-ready outputs.

[![CI](https://github.com/AmosBunde/ai-policy-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/AmosBunde/ai-policy-platform/actions/workflows/ci.yml)
[![Security](https://github.com/AmosBunde/ai-policy-platform/actions/workflows/security.yml/badge.svg)](https://github.com/AmosBunde/ai-policy-platform/actions/workflows/security.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Quickstart](#quickstart)
5. [Accessing the Stack](#accessing-the-stack)
6. [Testing](#testing)
7. [Deployment Workflow](#deployment-workflow)
8. [Documentation](#documentation)
9. [Project Structure](#project-structure)

---

## Overview

RegulatorAI is a microservices-based platform that:

- Ingests regulatory documents, news, and legal updates from global sources
- Uses LangGraph-orchestrated AI agents to summarize and extract key policy changes
- Ranks impact by region and product category
- Generates compliance reports and draft responses
- Supports full-text and semantic search across legal/policy data
- Provides real-time dashboards tracking regulatory risks and updates

---

## Architecture

Event-driven microservices behind a single API gateway. **Only the gateway is
exposed to the host in development** — every other service is reachable solely
on the internal Docker network (in production, a Caddy reverse proxy on
80/443 is the single entry point).

### Backend services

| Service | Internal port | Description |
|---------|---------------|-------------|
| Gateway | 8000 | Public API: JWT auth, RBAC, rate limiting, routing to internal services |
| Ingestion | 8001 | Document crawling (RSS/APIs/uploads), parsing, normalization; Celery workers |
| Agent | 8002 | LangGraph agents: summarizer, impact ranker, classifier, response drafter |
| Compliance | 8003 | Compliance report generation (PDF/DOCX), templates, status tracking |
| Search | 8004 | Hybrid search: Elasticsearch full-text + pgvector semantic similarity |
| Notification | 8005 | Watch rules and alerts via email, Slack, and webhooks |

### Frontend

`frontend/` — React 18 + TypeScript SPA (Vite, TailwindCSS, TanStack Query,
Zustand), served by nginx in containers, or by the Vite dev server locally.

### Infrastructure services (internal-only in dev)

PostgreSQL 16 (+pgvector), Redis 7, Elasticsearch 8, Celery worker/beat,
Prometheus, Grafana.

See [`docs/architecture/`](docs/architecture/) for C4 diagrams, sequence
diagrams, and ADRs.

---

## Tech Stack

**Backend:** Python 3.11+, FastAPI, LangGraph, Celery
**Frontend:** React 18, TypeScript, TailwindCSS, Recharts, TanStack Query
**AI/ML:** OpenAI API, LangChain, LangGraph
**Data:** PostgreSQL 16 + pgvector, Redis 7, Elasticsearch 8
**Infrastructure:** Docker Compose, Kubernetes (Helm), Terraform (AWS)
**CI/CD:** GitHub Actions → GHCR → gated Helm deploy
**Observability:** Prometheus, Grafana, structured JSON logging with request-ID propagation

---

## Quickstart

Prerequisites: Docker Desktop 4.x+ (Compose v2), Node.js 20 LTS, Python 3.11+.

```bash
# 1. Clone
git clone https://github.com/AmosBunde/ai-policy-platform.git
cd ai-policy-platform

# 2. Configure secrets (the file documents every variable;
#    generate secrets with the openssl hints inside it)
cp .env.example .env

# 3. Start the backend stack
docker compose up --build -d

# 4. Migrate and seed the database
make migrate && make seed

# 5. Run the frontend with hot reload (proxies /api to the gateway)
cd frontend && npm install && npm run dev
```

The dashboard is now at **http://localhost:3000** and the API at
**http://localhost:8000** (interactive docs at `/docs`).

---

## Accessing the Stack

| Component | URL | Notes |
|-----------|-----|-------|
| API Gateway | http://localhost:8000 | Only host-exposed backend service (`GATEWAY_PORT`) |
| API docs (Swagger / ReDoc) | http://localhost:8000/docs · /redoc | |
| Frontend (dev) | http://localhost:3000 | Via `npm run dev`; Vite proxies `/api` → gateway |
| Frontend (prod compose) | http://localhost | Via Caddy (`docker-compose.prod.yml`) |
| Prometheus, Grafana, Elasticsearch | — | Internal-only by design; see below |

To temporarily expose an internal service in development, add a local
`docker-compose.override.yml` (keep it out of version control):

```yaml
services:
  grafana:
    ports: ["3001:3000"]
  prometheus:
    ports: ["9090:9090"]
```

In production, Grafana is served through Caddy at `/grafana/*`, restricted to
internal/VPN IP ranges (see `infrastructure/docker/caddy/Caddyfile`).

---

## Testing

```bash
# Everything (backend suites + frontend), with a summary
./scripts/run_all_tests.sh

# One backend service
cd services/gateway-service && PYTHONPATH=../..:. python -m pytest tests -q

# Frontend unit tests / typecheck
cd frontend && npx vitest run && npx tsc --noEmit

# Integration tests in ephemeral containers
make test-integration

# End-to-end (Playwright)
cd frontend && npx playwright test

# Load tests (Locust)
cd scripts && locust -f load_test.py --host=http://localhost:8000
```

CI runs lint, all backend suites, frontend typecheck/tests/build, Docker
builds, and security scans on every pull request (see badges above).

---

## Deployment Workflow

### Pipeline (GitHub Actions)

1. **CI** (`.github/workflows/ci.yml`) — every PR: ruff (blocking on real
   errors), per-service pytest matrix, frontend typecheck + tests + build,
   Docker builds for all seven images.
2. **Security** (`.github/workflows/security.yml`) — every PR + weekly:
   Bandit (blocking at medium+ severity), Trivy vulnerability/misconfig/secret
   scans with SARIF upload to code scanning, npm audit.
3. **Publish & deploy** (`.github/workflows/deploy.yml`) — on push to `main`
   or a `v*.*.*` tag: builds and pushes all images to GHCR
   (`ghcr.io/amosbunde/ai-policy-platform/<service>`, tagged `sha-<commit>`,
   semver, and `latest`), scans the published image, then runs a **gated Helm
   deploy**: the job only runs when the `DEPLOY_ENABLED` repository variable
   is `true`, and executes inside the `production` environment — add required
   reviewers to that environment for a manual approval step.

Secrets to configure (repository or environment level): `KUBE_CONFIG`,
`JWT_SECRET`, `INTERNAL_SERVICE_TOKEN`, `DATABASE_URL`, `REDIS_URL`,
`ELASTICSEARCH_URL`, `OPENAI_API_KEY`.

### Infrastructure bootstrap (once per environment)

```bash
cd infrastructure/terraform
terraform init
terraform plan -var-file="prod.tfvars"
terraform apply -var-file="prod.tfvars"   # VPC, EKS, RDS, ElastiCache, Elasticsearch
aws eks update-kubeconfig --name regulatorai-cluster --region us-east-1
```

### Manual Helm deploy / rollback

```bash
# Deploy (all secret values are REQUIRED — the chart refuses to install
# with missing secrets rather than falling back to insecure defaults)
helm upgrade --install regulatorai infrastructure/kubernetes/helm/regulatorai \
  --namespace regulatorai --create-namespace \
  -f infrastructure/kubernetes/helm/regulatorai/values-prod.yaml \
  --set externalSecrets.jwtSecret="$(openssl rand -hex 32)" \
  --set externalSecrets.internalServiceToken="$(openssl rand -hex 32)" \
  --set externalSecrets.databaseUrl="postgresql+asyncpg://…" \
  --set externalSecrets.redisUrl="redis://…" \
  --set externalSecrets.elasticsearchUrl="http://…" \
  --set externalSecrets.openaiApiKey="sk-…"

# Verify / roll back
helm status regulatorai -n regulatorai
helm rollback regulatorai -n regulatorai   # previous revision, atomic
```

### Docker Compose on a single VM

```bash
cp .env.example .env && $EDITOR .env      # production values
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Caddy terminates TLS on 80/443 and is the only externally exposed service;
edit `infrastructure/docker/caddy/Caddyfile` for your domain.

### Production checklist

- [ ] All Helm secret values set (install fails loudly if any are missing)
- [ ] `INTERNAL_SERVICE_TOKEN` and `JWT_SECRET` are unique, ≥32 chars
- [ ] TLS configured (Caddy or ingress cert-manager)
- [ ] Database backups verified (`database-backup-cronjob.yaml`; see [Runbook](docs/runbook.md))
- [ ] HPA limits reviewed in `values-prod.yaml`
- [ ] Terraform state in a remote, locked backend

---

## Documentation

| Document | Description |
|----------|-------------|
| [User Guide](docs/user-guide.md) | Getting started, features, admin guide |
| [API Reference](docs/api-reference.md) | Endpoints, curl examples, rate limits |
| [Security](docs/security.md) | Security architecture, encryption, disclosure policy |
| [Architecture](docs/architecture/) | C4 diagrams, sequence diagrams, ADRs |
| [Runbook](docs/runbook.md) | Operational procedures: restart, backup, key rotation |
| [Troubleshooting](docs/troubleshooting.md) | Common issues and solutions |
| [Contributing](CONTRIBUTING.md) | Development setup, coding standards, security guidelines |
| [Changelog](CHANGELOG.md) | Version history |

---

## Project Structure

```
ai-policy-platform/
├── README.md
├── LICENSE
├── Makefile
├── .env.example
├── docker-compose.yml            # dev: gateway is the only exposed service
├── docker-compose.prod.yml       # prod overrides: Caddy, limits, restart policies
├── docker-compose.test.yml       # ephemeral integration-test stack
├── .github/
│   ├── workflows/                # ci.yml · security.yml · deploy.yml
│   ├── ISSUE_TEMPLATE/
│   └── dependabot.yml
├── docs/
│   └── architecture/             # C4 diagrams, sequence diagrams, ADRs
├── frontend/                     # React 18 + TS + Vite + Tailwind SPA
│   ├── tailwind.config.js
│   └── src/{components,pages,hooks,services,store,styles}
├── services/
│   ├── gateway-service/          # auth, RBAC, rate limiting, routing
│   ├── ingestion-service/        # crawlers, parsers, Celery tasks
│   ├── agent-service/            # LangGraph agent pipeline
│   ├── compliance-service/       # PDF/DOCX report generation
│   ├── search-service/           # Elasticsearch + pgvector hybrid search
│   └── notification-service/     # email/Slack/webhook alerts
├── shared/                       # models, config, security/logging/auth utils
├── infrastructure/
│   ├── docker/                   # Caddy, Prometheus, Grafana configs
│   ├── kubernetes/helm/          # regulatorai chart (+ values-prod.yaml)
│   └── terraform/                # VPC, EKS, RDS, ElastiCache, Elasticsearch
└── scripts/
    ├── run_all_tests.sh
    ├── seed_data.py
    └── load_test.py
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. Open a PR against
`main`; CI must pass and the PR template's verification checklist applies.

## License

MIT — see [LICENSE](LICENSE).
