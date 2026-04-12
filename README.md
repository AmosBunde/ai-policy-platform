# RegulatorAI — AI Policy Research & Compliance Automation Platform

> Enterprise-grade system using AI agents to monitor, analyze, and summarize global AI regulations and generate compliance-ready outputs.

![Architecture](docs/architecture/c4-context.md)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![React](https://img.shields.io/badge/react-18+-blue.svg)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Services](#services)
5. [Local Development Setup](#local-development-setup)
6. [Cloud Deployment](#cloud-deployment)
7. [Testing](#testing)
8. [Project Structure](#project-structure)

---

## Overview

RegulatorAI is a microservices-based platform that:

- Ingests regulatory documents, news, and legal updates from global sources
- Uses LangGraph-orchestrated AI agents to summarize and extract key policy changes
- Ranks impact by region and product category
- Generates compliance reports and draft responses
- Supports full-text and semantic search across legal/policy data
- Provides real-time dashboards tracking regulatory risks and updates
- Integrates with workflows for legal and policy teams

---

## Architecture

The platform follows an event-driven microservices architecture with the following core services:

| Service | Port | Description |
|---------|------|-------------|
| Gateway Service | 8000 | API Gateway, auth, rate limiting |
| Ingestion Service | 8001 | Document ingestion, parsing, normalization |
| Agent Service | 8002 | LangGraph AI agents for analysis |
| Compliance Service | 8003 | Report generation, draft responses |
| Search Service | 8004 | Elasticsearch + vector semantic search |
| Notification Service | 8005 | Alerts, webhooks, email notifications |
| Dashboard Service | 3000 | React frontend application |

See `docs/` directory for C4 diagrams, sequence diagrams, and detailed architecture docs.

---

## Tech Stack

**Backend:** Python 3.11+, FastAPI, LangGraph, Celery
**Frontend:** React 18, TypeScript, TailwindCSS, Recharts, TanStack Query
**AI/ML:** OpenAI API, LangChain, LangGraph
**Database:** PostgreSQL 16 (primary), Redis 7 (cache/queue)
**Search:** Elasticsearch 8.x (full-text), pgvector (semantic)
**Infrastructure:** Docker, Docker Compose, Kubernetes (Helm), Terraform
**CI/CD:** GitHub Actions
**Monitoring:** Prometheus, Grafana, structured logging

---

## Services

### 1. Gateway Service (`services/gateway-service`)
API Gateway handling authentication (JWT), rate limiting, request routing, and CORS.

### 2. Ingestion Service (`services/ingestion-service`)
Crawls and ingests regulatory documents from RSS feeds, government APIs, and uploaded PDFs. Normalizes content into a unified schema. Uses Celery for async processing.

### 3. Agent Service (`services/agent-service`)
LangGraph-orchestrated multi-agent system:
- **Summarizer Agent**: Extracts key policy changes
- **Impact Ranker Agent**: Scores impact by region/product
- **Classifier Agent**: Categorizes by regulatory domain
- **Drafter Agent**: Generates compliance response drafts

### 4. Compliance Service (`services/compliance-service`)
Generates structured compliance reports (PDF, DOCX), manages report templates, tracks compliance status per regulation.

### 5. Search Service (`services/search-service`)
Dual search: Elasticsearch for full-text keyword search, pgvector for semantic similarity. Supports faceted filtering by jurisdiction, date, category.

### 6. Notification Service (`services/notification-service`)
Event-driven alerts via email, Slack, and webhooks. Users configure watch rules (e.g., "notify me when EU AI Act changes").

---

## Local Development Setup

### Prerequisites

- Docker Desktop 4.x+ with Docker Compose v2
- Python 3.11+
- Node.js 20 LTS
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/regulatorai.git
cd regulatorai
```

### Step 2: Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env with your API keys:
#   OPENAI_API_KEY=sk-...
#   POSTGRES_PASSWORD=your_secure_password
#   REDIS_PASSWORD=your_redis_password
#   JWT_SECRET=your_jwt_secret
#   ELASTICSEARCH_PASSWORD=your_es_password
```

### Step 3: Start All Services with Docker Compose

```bash
# Build and start all services
docker compose up --build -d

# Verify all services are running
docker compose ps

# Check logs
docker compose logs -f
```

### Step 4: Initialize the Database

```bash
# Run database migrations
docker compose exec gateway-service alembic upgrade head

# Seed initial data (regulatory sources, default templates)
docker compose exec gateway-service python -m scripts.seed_data
```

### Step 5: Access the Application

| Component | URL |
|-----------|-----|
| Frontend Dashboard | http://localhost:3000 |
| API Gateway | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |
| Elasticsearch | http://localhost:9200 |
| Redis Commander | http://localhost:8081 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 |

### Step 6: Run Tests

```bash
# Run all backend tests
docker compose exec gateway-service pytest --cov=src tests/

# Run frontend tests
cd frontend && npm test

# Run integration tests
docker compose -f docker-compose.test.yml up --abort-on-container-exit
```

---

## Cloud Deployment

### Option A: Docker Compose on a Cloud VM (AWS EC2 / GCP Compute / Azure VM)

```bash
# 1. SSH into your cloud VM
ssh user@your-vm-ip

# 2. Install Docker and Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 3. Clone and configure
git clone https://github.com/your-org/regulatorai.git
cd regulatorai
cp .env.example .env
nano .env  # Set production values

# 4. Deploy with production compose file
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 5. Set up SSL with Caddy/Nginx reverse proxy
# See infrastructure/docker/caddy/Caddyfile for configuration
```

### Option B: Kubernetes (EKS / GKE / AKS)

```bash
# 1. Configure kubectl for your cluster
aws eks update-kubeconfig --name regulatorai-cluster --region us-east-1
# OR
gcloud container clusters get-credentials regulatorai-cluster --zone us-central1-a

# 2. Create namespace
kubectl create namespace regulatorai

# 3. Apply secrets
kubectl apply -f infrastructure/kubernetes/secrets.yml -n regulatorai

# 4. Deploy with Helm
helm install regulatorai infrastructure/kubernetes/helm/regulatorai \
  --namespace regulatorai \
  --values infrastructure/kubernetes/helm/regulatorai/values-prod.yaml

# 5. Verify deployment
kubectl get pods -n regulatorai
kubectl get services -n regulatorai
```

### Option C: Terraform (Infrastructure as Code)

```bash
# 1. Initialize Terraform
cd infrastructure/terraform
terraform init

# 2. Plan the deployment
terraform plan -var-file="prod.tfvars"

# 3. Apply
terraform apply -var-file="prod.tfvars"

# 4. Get outputs (endpoints, etc.)
terraform output
```

---

## Testing

### Unit Tests
```bash
# Per-service
cd services/agent-service && pytest tests/unit/ -v

# All services
./scripts/run_all_tests.sh
```

### Integration Tests
```bash
docker compose -f docker-compose.test.yml up --abort-on-container-exit
```

### End-to-End Tests
```bash
cd frontend && npx playwright test
```

### Load Tests
```bash
cd scripts && locust -f load_test.py --host=http://localhost:8000
```

---

## Project Structure

```
regulatorai/
├── README.md
├── docker-compose.yml
├── docker-compose.prod.yml
├── docker-compose.test.yml
├── .env.example
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   └── deploy.yml
│   └── ISSUE_TEMPLATE/
├── docs/
│   ├── architecture/
│   │   ├── c4-context.md
│   │   ├── c4-container.md
│   │   ├── c4-component.md
│   │   ├── sequence-diagrams.md
│   │   └── architecture-decision-records.md
│   └── diagrams/
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── hooks/
│       ├── services/
│       ├── store/
│       └── types/
├── services/
│   ├── gateway-service/
│   ├── ingestion-service/
│   ├── agent-service/
│   ├── compliance-service/
│   ├── search-service/
│   └── notification-service/
├── shared/
│   ├── models/
│   ├── utils/
│   └── config/
├── infrastructure/
│   ├── docker/
│   ├── kubernetes/
│   └── terraform/
└── scripts/
    ├── create_issues.sh
    ├── run_all_tests.sh
    └── seed_data.py
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.
