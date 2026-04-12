# Architecture Decision Records (ADRs)

## ADR-001: Microservices Over Monolith

**Status:** Accepted
**Date:** 2026-04-13

**Context:** The platform requires independent scaling of compute-intensive AI agents vs. lightweight CRUD operations, different deployment cadences per domain, and team autonomy.

**Decision:** Adopt event-driven microservices architecture with 6 backend services + 1 frontend.

**Consequences:** Higher operational complexity offset by independent scaling, fault isolation, and team autonomy. Redis Pub/Sub for inter-service communication keeps infrastructure simple while maintaining loose coupling.

---

## ADR-002: LangGraph for Agent Orchestration

**Status:** Accepted

**Context:** Need stateful, multi-step AI workflows with conditional branching, retries, and observability.

**Decision:** Use LangGraph (over raw LangChain chains or custom orchestration) for the agent pipeline.

**Consequences:** Built-in state management, checkpointing, human-in-the-loop hooks, and visualization. Lock-in to LangChain ecosystem is acceptable given the rapid development pace.

---

## ADR-003: Hybrid Search (Elasticsearch + pgvector)

**Status:** Accepted

**Context:** Legal search requires both exact keyword matching (statute numbers, case citations) and semantic similarity (concept-based queries).

**Decision:** Dual search with Reciprocal Rank Fusion (RRF) merging. Elasticsearch for BM25 full-text, pgvector for embedding similarity.

**Consequences:** Higher infrastructure cost (running ES cluster) justified by superior search quality. RRF provides a tunable blending mechanism without training a custom ranker.

---

## ADR-004: FastAPI for All Backend Services

**Status:** Accepted

**Context:** Need async-capable, high-performance Python web framework with auto-generated OpenAPI docs.

**Decision:** FastAPI for all services (over Flask, Django, or mixed frameworks).

**Consequences:** Consistent developer experience, shared middleware patterns, native async/await for I/O-bound operations. Pydantic v2 for schema validation across services.

---

## ADR-005: Redis for Caching and Pub/Sub

**Status:** Accepted

**Context:** Need lightweight inter-service messaging and a caching layer. Kafka is overkill for current scale.

**Decision:** Redis 7 for both caching (TTL-based) and Pub/Sub messaging.

**Consequences:** Simpler ops than Kafka. At-most-once delivery is acceptable for notifications (email/Slack have their own retry). If we outgrow Pub/Sub, migration to Redis Streams or Kafka is straightforward.

---

## ADR-006: PostgreSQL with pgvector for Primary Data Store

**Status:** Accepted

**Context:** Need relational integrity for regulatory documents, user data, and compliance records, plus vector similarity search.

**Decision:** PostgreSQL 16 with pgvector extension for unified relational + vector storage.

**Consequences:** Single database for structured data and embeddings reduces operational burden. pgvector HNSW indexes provide good-enough ANN performance for our scale (sub-million vectors).

---

## ADR-007: React + TypeScript for Frontend

**Status:** Accepted

**Context:** Enterprise dashboard with complex state, real-time updates, and data-heavy visualizations.

**Decision:** React 18 with TypeScript, TailwindCSS, TanStack Query for data fetching, Recharts for charts.

**Consequences:** Mature ecosystem, strong typing for maintainability, component-based architecture for team collaboration.
