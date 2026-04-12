# C4 Model — Component Diagram (Agent Service)

## Agent Service Components

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Agent Service                                 │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐   │
│  │                   Agent Orchestrator                          │   │
│  │                   (LangGraph StateGraph)                      │   │
│  │                                                               │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │   │
│  │  │ Router Node │──│ Summarizer  │──│ Classifier  │          │   │
│  │  │             │  │ Node        │  │ Node        │          │   │
│  │  └─────────────┘  └─────────────┘  └──────┬──────┘          │   │
│  │                                           │                  │   │
│  │                          ┌────────────────┼────────┐         │   │
│  │                          ▼                ▼        │         │   │
│  │                   ┌─────────────┐  ┌─────────────┐│         │   │
│  │                   │ Impact      │  │ Drafter     ││         │   │
│  │                   │ Ranker Node │  │ Node        ││         │   │
│  │                   └─────────────┘  └─────────────┘│         │   │
│  │                          │                │        │         │   │
│  │                          ▼                ▼        │         │   │
│  │                   ┌──────────────────────────────┐ │         │   │
│  │                   │     Aggregator Node          │ │         │   │
│  │                   │  (Merges all agent outputs)  │ │         │   │
│  │                   └──────────────────────────────┘ │         │   │
│  └───────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │
│  │ LLM Client     │  │ Prompt         │  │ Token Tracker  │         │
│  │ (OpenAI API)   │  │ Templates      │  │ & Cost Mgmt    │         │
│  │                │  │ (Jinja2)       │  │                │         │
│  └────────────────┘  └────────────────┘  └────────────────┘         │
│                                                                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │
│  │ State Manager  │  │ Retry Handler  │  │ Callback       │         │
│  │ (Agent State)  │  │ (Exp Backoff)  │  │ Handler        │         │
│  └────────────────┘  └────────────────┘  └────────────────┘         │
└──────────────────────────────────────────────────────────────────────┘
```

## Agent State Schema

```python
class AgentState(TypedDict):
    document_id: str
    raw_content: str
    metadata: dict
    summary: Optional[str]
    key_changes: Optional[list[str]]
    classification: Optional[dict]
    impact_scores: Optional[dict]
    draft_response: Optional[str]
    errors: list[str]
    token_usage: dict
    current_step: str
```

## LangGraph Flow

```
START
  │
  ▼
[Router] ──── Determines processing path based on document type
  │
  ├──► [Summarizer] ──── Extracts key changes, timelines, affected parties
  │         │
  │         ▼
  │    [Classifier] ──── Tags: privacy, safety, IP, antitrust, export, etc.
  │         │
  │         ├──► [Impact Ranker] ──── Scores 1-10 by region × product matrix
  │         │
  │         └──► [Drafter] ──── Generates compliance response template
  │                   │
  │                   ▼
  └────────────► [Aggregator] ──── Merges outputs, validates, persists
                      │
                      ▼
                    END ──── Publishes enrichment event to Redis
```

## Component Details

### Router Node
- Inspects document metadata (source, type, jurisdiction)
- Determines which agents to invoke (not all docs need all agents)
- Handles document language detection

### Summarizer Node
- Uses structured output prompts for consistent extraction
- Outputs: executive summary, key changes list, effective dates, affected entities
- Handles multi-page documents via chunking with overlap

### Classifier Node
- Multi-label classification across regulatory domains
- Confidence scores per label
- Jurisdiction detection (EU, US-Federal, US-State, UK, etc.)

### Impact Ranker Node
- Scoring matrix: regions (rows) × product categories (columns)
- Each cell scored 1-10 with justification text
- Urgency flag for high-impact changes

### Drafter Node
- Template-based response generation
- Adapts tone for different audiences (board, legal, engineering)
- Includes recommended actions and deadlines

### Aggregator Node
- Merges all agent outputs into unified enrichment record
- Validates completeness and consistency
- Persists to PostgreSQL
- Publishes event for downstream services
