# Sequence Diagrams

## 1. Document Ingestion and Processing Flow

```
User/Scheduler    Ingestion     Redis       Agent       PostgreSQL    Elasticsearch
     │            Service       Pub/Sub     Service         │              │
     │                │            │           │            │              │
     │  Trigger       │            │           │            │              │
     │  Crawl         │            │           │            │              │
     ├───────────────►│            │           │            │              │
     │                │            │           │            │              │
     │                │ Fetch doc  │           │            │              │
     │                │ from source│           │            │              │
     │                │────────────┤           │            │              │
     │                │            │           │            │              │
     │                │ Parse &    │           │            │              │
     │                │ Normalize  │           │            │              │
     │                │────┐       │           │            │              │
     │                │    │       │           │            │              │
     │                │◄───┘       │           │            │              │
     │                │            │           │            │              │
     │                │ Dedup      │           │            │              │
     │                │ Check      │           │            │              │
     │                │───────────────────────────────────►│              │
     │                │◄──────────────────────────────────│              │
     │                │            │           │            │              │
     │                │ Store raw  │           │            │              │
     │                │ document   │           │            │              │
     │                │───────────────────────────────────►│              │
     │                │            │           │            │              │
     │                │ Publish    │           │            │              │
     │                │ new_doc    │           │            │              │
     │                │ event      │           │            │              │
     │                │───────────►│           │            │              │
     │                │            │           │            │              │
     │                │            │ Subscribe │            │              │
     │                │            │ new_doc   │            │              │
     │                │            │──────────►│            │              │
     │                │            │           │            │              │
     │                │            │           │ Run        │              │
     │                │            │           │ LangGraph  │              │
     │                │            │           │ Pipeline   │              │
     │                │            │           │───┐        │              │
     │                │            │           │   │        │              │
     │                │            │           │   │ Call    │              │
     │                │            │           │   │ OpenAI  │              │
     │                │            │           │   │        │              │
     │                │            │           │◄──┘        │              │
     │                │            │           │            │              │
     │                │            │           │ Store      │              │
     │                │            │           │ enrichment │              │
     │                │            │           │───────────►│              │
     │                │            │           │            │              │
     │                │            │           │ Index      │              │
     │                │            │           │────────────┼─────────────►│
     │                │            │           │            │              │
     │                │            │           │ Publish    │              │
     │                │            │           │ enriched   │              │
     │                │            │           │ event      │              │
     │                │            │           │──►│        │              │
     │                │            │           │   │        │              │
```

## 2. User Search Flow

```
User         Dashboard      Gateway       Search        Elasticsearch   PostgreSQL
  │              │            Service       Service          │              │
  │  Search      │              │             │              │              │
  │  "EU AI Act" │              │             │              │              │
  ├─────────────►│              │             │              │              │
  │              │              │             │              │              │
  │              │ POST /search │             │              │              │
  │              │─────────────►│             │              │              │
  │              │              │             │              │              │
  │              │              │ Validate    │              │              │
  │              │              │ JWT + RBAC  │              │              │
  │              │              │──┐          │              │              │
  │              │              │◄─┘          │              │              │
  │              │              │             │              │              │
  │              │              │ Forward     │              │              │
  │              │              │────────────►│              │              │
  │              │              │             │              │              │
  │              │              │             │ Full-text    │              │
  │              │              │             │ search       │              │
  │              │              │             │─────────────►│              │
  │              │              │             │◄────────────│              │
  │              │              │             │              │              │
  │              │              │             │ Semantic     │              │
  │              │              │             │ search       │              │
  │              │              │             │──────────────┼─────────────►│
  │              │              │             │◄─────────────┼─────────────│
  │              │              │             │              │              │
  │              │              │             │ Merge &      │              │
  │              │              │             │ Rank (RRF)   │              │
  │              │              │             │──┐           │              │
  │              │              │             │◄─┘           │              │
  │              │              │             │              │              │
  │              │◄────────────┤◄────────────│              │              │
  │◄─────────────│              │             │              │              │
  │  Results     │              │             │              │              │
```

## 3. Compliance Report Generation Flow

```
User        Dashboard      Gateway      Compliance     Agent        PostgreSQL
  │             │            Service       Service      Service          │
  │ Generate    │              │             │            │              │
  │ Report      │              │             │            │              │
  ├────────────►│              │             │            │              │
  │             │ POST         │             │            │              │
  │             │ /reports     │             │            │              │
  │             │─────────────►│             │            │              │
  │             │              │             │            │              │
  │             │              │ Auth +      │            │              │
  │             │              │ Route       │            │              │
  │             │              │────────────►│            │              │
  │             │              │             │            │              │
  │             │              │             │ Fetch      │              │
  │             │              │             │ enriched   │              │
  │             │              │             │ data       │              │
  │             │              │             │───────────────────────────►│
  │             │              │             │◄──────────────────────────│
  │             │              │             │            │              │
  │             │              │             │ Request    │              │
  │             │              │             │ draft      │              │
  │             │              │             │───────────►│              │
  │             │              │             │            │ Call LLM     │
  │             │              │             │            │──┐           │
  │             │              │             │            │◄─┘           │
  │             │              │             │◄──────────│              │
  │             │              │             │            │              │
  │             │              │             │ Generate   │              │
  │             │              │             │ PDF/DOCX   │              │
  │             │              │             │──┐         │              │
  │             │              │             │◄─┘         │              │
  │             │              │             │            │              │
  │             │              │             │ Store      │              │
  │             │              │             │ report     │              │
  │             │              │             │───────────────────────────►│
  │             │◄────────────┤◄────────────│            │              │
  │◄────────────│              │             │            │              │
  │ Report URL  │              │             │            │              │
```

## 4. Notification Watch Rule Flow

```
User        Dashboard      Gateway     Notification   Redis        Agent
  │             │           Service       Service      Pub/Sub      Service
  │ Create      │              │             │            │            │
  │ Watch Rule  │              │             │            │            │
  │ "EU privacy"│              │             │            │            │
  ├────────────►│              │             │            │            │
  │             │─────────────►│             │            │            │
  │             │              │────────────►│            │            │
  │             │              │             │ Store rule │            │
  │             │              │             │──┐         │            │
  │             │◄────────────┤◄────────────│◄─┘         │            │
  │◄────────────│              │             │            │            │
  │             │              │             │            │            │
  │             │              │             │            │            │
  │  ... Later, new document arrives ...    │            │            │
  │             │              │             │            │            │
  │             │              │             │            │ Enrichment │
  │             │              │             │            │ complete   │
  │             │              │             │            │◄───────────│
  │             │              │             │            │            │
  │             │              │             │ Event:     │            │
  │             │              │             │ doc_enriched            │
  │             │              │             │◄───────────│            │
  │             │              │             │            │            │
  │             │              │             │ Match      │            │
  │             │              │             │ rules      │            │
  │             │              │             │──┐         │            │
  │             │              │             │◄─┘         │            │
  │             │              │             │            │            │
  │             │              │             │ Send email │            │
  │  ◄──────────┼──────────────┼─────────────│            │            │
  │  Email      │              │             │            │            │
  │  notification              │             │            │            │
```

## 5. User Authentication Flow

```
User         Dashboard      Gateway       PostgreSQL     Redis
  │              │            Service          │            │
  │  Login       │              │              │            │
  │  (email/pwd) │              │              │            │
  ├─────────────►│              │              │            │
  │              │ POST /auth   │              │            │
  │              │ /login       │              │            │
  │              │─────────────►│              │            │
  │              │              │              │            │
  │              │              │ Verify       │            │
  │              │              │ credentials  │            │
  │              │              │─────────────►│            │
  │              │              │◄────────────│            │
  │              │              │              │            │
  │              │              │ Generate     │            │
  │              │              │ JWT pair     │            │
  │              │              │──┐           │            │
  │              │              │◄─┘           │            │
  │              │              │              │            │
  │              │              │ Cache        │            │
  │              │              │ session      │            │
  │              │              │─────────────────────────►│
  │              │              │              │            │
  │              │◄────────────│              │            │
  │◄─────────────│              │              │            │
  │  JWT tokens  │              │              │            │
  │              │              │              │            │
  │  Subsequent  │              │              │            │
  │  API call    │              │              │            │
  │  + Bearer    │              │              │            │
  ├─────────────►│              │              │            │
  │              │─────────────►│              │            │
  │              │              │ Validate JWT │            │
  │              │              │──┐           │            │
  │              │              │◄─┘           │            │
  │              │              │ Check cache  │            │
  │              │              │─────────────────────────►│
  │              │              │◄────────────────────────│
  │              │              │              │            │
  │              │◄────────────│              │            │
  │◄─────────────│              │              │            │
```
