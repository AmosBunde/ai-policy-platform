---
name: regulatorai-implementation
description: Skill for implementing the RegulatorAI AI Policy Research & Compliance Automation Platform. Use this skill whenever working on any issue related to the RegulatorAI project, including backend services (FastAPI, LangGraph agents, Elasticsearch, Celery), frontend (React 18, TypeScript, TailwindCSS), infrastructure (Docker, Kubernetes, Terraform), or any regulatory compliance automation feature. Trigger on mentions of regulatory documents, compliance reports, AI agents for policy analysis, ingestion pipelines, or the RegulatorAI platform.
---

# RegulatorAI Implementation Skill

## Project Overview

RegulatorAI is an enterprise-grade microservices platform that uses AI agents to monitor, analyze, and summarize global AI regulations and generate compliance-ready outputs.

## Architecture

- **6 Backend Services**: Gateway (8000), Ingestion (8001), Agent (8002), Compliance (8003), Search (8004), Notification (8005)
- **Frontend**: React 18 + TypeScript + TailwindCSS on port 3000
- **Data Stores**: PostgreSQL 16 + pgvector, Redis 7, Elasticsearch 8
- **AI Pipeline**: LangGraph with 5 agents (Router, Summarizer, Classifier, Impact Ranker, Drafter)
- **Async**: Celery workers for ingestion, Redis Pub/Sub for inter-service events

## Tech Stack Reference

### Backend (per service)
- Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), asyncpg
- Alembic for migrations
- structlog for logging
- prometheus_client for metrics
- pytest + pytest-asyncio for tests

### Agent Service Specific
- LangGraph StateGraph for orchestration
- LangChain + OpenAI for LLM calls
- tiktoken for token counting
- Jinja2 for prompt templates

### Frontend
- Vite + React 18 + TypeScript (strict mode)
- TailwindCSS with custom enterprise theme
- React Router v6
- TanStack Query for server state
- Zustand for client state
- Recharts for data visualization
- Axios with JWT interceptor
- Lucide React for icons

### Design System
- **Primary**: Deep Navy `#0F172A`
- **Secondary**: Slate `#1E293B`
- **Accent**: Amber `#F59E0B`
- **Success**: Emerald `#10B981`
- **Danger**: Rose `#F43F5E`
- **Surface**: `#0F172A` (dark), `#FFFFFF` (light)
- **Typography**: DM Sans (headings), Inter (body) — exception to generic rule due to enterprise context
- **Cards**: Glass morphism with `backdrop-blur-xl bg-white/5 border border-white/10`

## Directory Structure

```
regulatorai/
├── services/
│   ├── gateway-service/src/          # Auth, routing, rate limiting
│   ├── ingestion-service/src/        # Crawlers, parsers, Celery
│   ├── agent-service/src/            # LangGraph pipeline
│   ├── compliance-service/src/       # Report generation
│   ├── search-service/src/           # ES + pgvector hybrid
│   └── notification-service/src/     # Watch rules, email, Slack
├── shared/
│   ├── models/schemas.py             # Pydantic models
│   ├── models/orm.py                 # SQLAlchemy ORM
│   ├── config/settings.py            # Env-based config
│   └── utils/                        # Security, events, logging
├── frontend/src/
│   ├── components/                   # Reusable UI components
│   ├── pages/                        # Route pages
│   ├── hooks/                        # Custom hooks
│   ├── services/api.ts               # Axios client
│   ├── store/                        # Zustand stores
│   └── types/                        # TypeScript types
├── infrastructure/
│   ├── docker/                       # Compose, Prometheus, Grafana
│   ├── kubernetes/helm/              # Helm charts
│   └── terraform/                    # IaC modules
├── docs/architecture/                # C4, sequences, ADRs
└── scripts/                          # Issue creation, Claude prompts
```

## Implementation Standards

### Python Services
1. Every endpoint must have Pydantic request/response models
2. All DB operations use async SQLAlchemy sessions
3. Every service exposes `/health` and `/metrics` endpoints
4. Use dependency injection for auth, DB sessions, config
5. Structured logging with request_id correlation
6. Tests use pytest-asyncio with httpx AsyncClient

### React Frontend
1. All components are functional with TypeScript props interfaces
2. API calls go through TanStack Query hooks (never raw fetch in components)
3. Forms use react-hook-form + zod validation
4. Loading states use skeleton components (no spinners)
5. All pages are responsive (desktop-first)
6. Dark/light theme via CSS custom properties

### Git Workflow
1. Branch naming: `feature/{issue-number}-{short-description}`
2. Commit messages follow Conventional Commits
3. Every PR references its issue with `Closes #{number}`
4. Squash merge to main

### Testing
- Unit tests: per-module, mocked dependencies
- Integration tests: docker-compose.test.yml, real DB
- E2E tests: Playwright for frontend flows
- Load tests: Locust for API throughput
- Minimum coverage: 80% backend, 70% frontend

## Key Implementation Patterns

### Inter-Service Communication
```python
# Publishing events
from shared.utils.events import RedisEventPublisher
publisher = RedisEventPublisher(redis_url)
await publisher.publish("document.ingested", DocumentEvent(...))

# Subscribing to events
from shared.utils.events import RedisEventSubscriber
subscriber = RedisEventSubscriber(redis_url)
await subscriber.subscribe("document.ingested", handle_new_document)
```

### LangGraph Pipeline
```python
from langgraph.graph import StateGraph, END

graph = StateGraph(AgentState)
graph.add_node("router", router_node)
graph.add_node("summarizer", summarizer_node)
graph.add_node("classifier", classifier_node)
graph.add_node("impact_ranker", impact_ranker_node)
graph.add_node("drafter", drafter_node)
graph.add_node("aggregator", aggregator_node)

graph.set_entry_point("router")
graph.add_edge("router", "summarizer")
graph.add_edge("summarizer", "classifier")
graph.add_conditional_edges("classifier", route_by_impact, {
    "high": "impact_ranker",
    "low": "aggregator"
})
graph.add_edge("impact_ranker", "drafter")
graph.add_edge("drafter", "aggregator")
graph.add_edge("aggregator", END)

pipeline = graph.compile()
```

### Hybrid Search (RRF)
```python
def reciprocal_rank_fusion(es_results, vector_results, k=60):
    scores = {}
    for rank, doc in enumerate(es_results):
        scores[doc.id] = scores.get(doc.id, 0) + 1 / (k + rank + 1)
    for rank, doc in enumerate(vector_results):
        scores[doc.id] = scores.get(doc.id, 0) + 1 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

## Issue-to-Branch Mapping

| Issue | Branch | Service |
|-------|--------|---------|
| #1 | feature/001-project-scaffold | infra |
| #2 | feature/002-database-schema | shared/db |
| #3 | feature/003-shared-library | shared |
| #4 | feature/004-gateway-service | gateway |
| #5 | feature/005-monitoring-stack | infra |
| #6 | feature/006-ingestion-service | ingestion |
| #7 | feature/007-agent-service | agent |
| #8 | feature/008-search-service | search |
| #9 | feature/009-compliance-service | compliance |
| #10 | feature/010-notification-service | notification |
| #11 | feature/011-frontend-scaffold | frontend |
| #12 | feature/012-auth-pages | frontend |
| #13 | feature/013-dashboard-page | frontend |
| #14 | feature/014-document-explorer | frontend |
| #15 | feature/015-search-page | frontend |
| #16 | feature/016-reports-page | frontend |
| #17 | feature/017-settings-page | frontend |
| #18 | feature/018-testing-suite | all |
| #19 | feature/019-production-deployment | infra |
| #20 | feature/020-documentation | docs |
