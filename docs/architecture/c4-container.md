# C4 Model — Container Diagram

## Container Architecture

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                           RegulatorAI Platform                                 │
│                                                                                │
│  ┌─────────────────────────────────────────────────────────────┐               │
│  │                    Frontend (React 18 + TS)                 │               │
│  │                    Port: 3000                               │               │
│  │  Dashboard, Search UI, Report Viewer, Settings              │               │
│  └──────────────────────────┬──────────────────────────────────┘               │
│                             │ HTTPS/REST                                       │
│                             ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────┐               │
│  │              API Gateway (FastAPI) — Port 8000              │               │
│  │  JWT Auth │ Rate Limiting │ Request Routing │ CORS          │               │
│  └──────┬──────────┬──────────┬──────────┬──────────┬──────────┘               │
│         │          │          │          │          │                           │
│         ▼          ▼          ▼          ▼          ▼                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐             │
│  │Ingestion │ │ Agent    │ │Compliance│ │ Search   │ │Notific.  │             │
│  │Service   │ │ Service  │ │Service   │ │ Service  │ │Service   │             │
│  │Port:8001 │ │Port:8002 │ │Port:8003 │ │Port:8004 │ │Port:8005 │             │
│  │          │ │          │ │          │ │          │ │          │             │
│  │ Crawlers │ │ LangGraph│ │ Report   │ │ ES +     │ │ Email    │             │
│  │ Parsers  │ │ Agents   │ │ Gen      │ │ pgvector │ │ Slack    │             │
│  │ Celery   │ │ Chains   │ │ Template │ │ Facets   │ │ Webhook  │             │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘             │
│       │            │            │            │            │                    │
│       └────────────┴────────────┴─────┬──────┴────────────┘                    │
│                                       │                                        │
│              ┌────────────────────────┼────────────────────────┐               │
│              ▼                        ▼                        ▼               │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐             │
│  │   PostgreSQL 16  │  │    Redis 7       │  │ Elasticsearch 8  │             │
│  │   + pgvector     │  │   Cache + Queue  │  │   Full-text      │             │
│  │   Port: 5432     │  │   Port: 6379     │  │   Port: 9200     │             │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘             │
│                                                                                │
│  ┌──────────────────────────────────────────────────────────────┐              │
│  │              Observability Stack                             │              │
│  │  Prometheus (9090) │ Grafana (3001) │ Structured Logging     │              │
│  └──────────────────────────────────────────────────────────────┘              │
└────────────────────────────────────────────────────────────────────────────────┘
```

## Container Responsibilities

### API Gateway (FastAPI)
- JWT token validation and refresh
- Role-based access control (RBAC)
- Rate limiting (token bucket algorithm)
- Request routing to downstream services
- OpenAPI documentation auto-generation
- Health check aggregation

### Ingestion Service
- Scheduled crawlers (APScheduler) for regulatory sources
- Document parsers: PDF (PyMuPDF), HTML (BeautifulSoup), XML
- Content normalization into unified `RegulatoryDocument` schema
- Deduplication using content hashing (SHA-256)
- Celery task queue for async processing
- Source health monitoring

### Agent Service (LangGraph)
- Multi-agent orchestration via LangGraph StateGraph
- **Summarizer**: Extracts key changes, affected parties, timelines
- **Impact Ranker**: Scores 1-10 impact by region and product category
- **Classifier**: Tags by regulatory domain (privacy, safety, IP, etc.)
- **Drafter**: Generates compliance response drafts
- Retry logic with exponential backoff for LLM calls
- Token usage tracking and cost management

### Compliance Service
- Report templates (Jinja2-based)
- PDF and DOCX generation
- Compliance checklist tracking per regulation
- Version history for compliance documents
- Export to common formats

### Search Service
- Elasticsearch for full-text keyword search with BM25
- pgvector for semantic embedding search
- Hybrid search combining both approaches
- Faceted filtering: jurisdiction, date range, category, status
- Search suggestions and autocomplete

### Notification Service
- Event-driven architecture (Redis Pub/Sub)
- User-configurable watch rules
- Multi-channel delivery: email (SMTP), Slack (webhook), in-app
- Notification history and read tracking
- Digest scheduling (daily, weekly)

## Data Flow

```
1. Sources → Ingestion Service → PostgreSQL (raw + normalized docs)
2. New doc event → Redis Pub/Sub → Agent Service
3. Agent Service → LLM analysis → PostgreSQL (enriched metadata)
4. Enriched doc → Search Service → Elasticsearch index
5. Enriched doc → Notification Service → User alerts
6. User → Dashboard → Gateway → Search/Compliance → Response
```
