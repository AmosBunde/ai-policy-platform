# C4 Model — Context Diagram

## System Context

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          External Systems                              │
│                                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ Government   │  │ Legal News   │  │ RSS/Atom     │                  │
│  │ Regulatory   │  │ APIs         │  │ Feeds        │                  │
│  │ Portals      │  │ (Reuters,    │  │              │                  │
│  │ (EU, US,     │  │  Bloomberg)  │  │              │                  │
│  │  UK, etc.)   │  │              │  │              │                  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  │
│         │                 │                 │                           │
│         └────────────────┼────────────────┘                            │
│                          │                                              │
│                          ▼                                              │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                                                                   │  │
│  │                    RegulatorAI Platform                            │  │
│  │                                                                   │  │
│  │   Monitors, analyzes, and summarizes global AI regulations        │  │
│  │   using AI agents. Generates compliance reports and draft         │  │
│  │   responses. Provides search and dashboards for legal teams.      │  │
│  │                                                                   │  │
│  └──────────────────────────┬────────────────────────────────────────┘  │
│                             │                                           │
│              ┌──────────────┼──────────────┐                            │
│              ▼              ▼              ▼                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ Compliance   │  │ Policy       │  │ Legal        │                  │
│  │ Officers     │  │ Analysts     │  │ Teams        │                  │
│  │              │  │              │  │              │                  │
│  │ [Person]     │  │ [Person]     │  │ [Person]     │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│                                                                        │
│  ┌──────────────┐  ┌──────────────┐                                    │
│  │ OpenAI API   │  │ Email/Slack  │                                    │
│  │ (LLM)       │  │ (Notif.)     │                                    │
│  └──────────────┘  └──────────────┘                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

## Actors

| Actor | Description |
|-------|-------------|
| Compliance Officer | Reviews compliance reports, manages regulatory status |
| Policy Analyst | Searches regulations, analyzes impact, creates policy briefs |
| Legal Team | Drafts responses, reviews AI-generated compliance outputs |
| System Admin | Configures data sources, manages users and permissions |

## External Systems

| System | Integration | Description |
|--------|-------------|-------------|
| Government Portals | HTTP/API Crawl | EU AI Act portal, US Federal Register, UK ICO |
| Legal News APIs | REST API | Reuters, Bloomberg Law, LexisNexis feeds |
| RSS/Atom Feeds | RSS Parser | Policy blogs, regulatory body announcements |
| OpenAI API | REST API | GPT-4 for summarization, classification, drafting |
| Email/Slack | SMTP/Webhook | Notification delivery channels |
