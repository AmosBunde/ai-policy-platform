# RegulatorAI User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Searching Regulations](#searching-regulations)
4. [Viewing Documents and Enrichments](#viewing-documents-and-enrichments)
5. [Creating Compliance Reports](#creating-compliance-reports)
6. [Setting Up Watch Rules](#setting-up-watch-rules)
7. [Admin: Managing Sources and Users](#admin-managing-sources-and-users)

---

## Getting Started

### First Login

1. Navigate to the RegulatorAI dashboard at your organization's URL (e.g., `https://app.regulatorai.com`).
2. Enter your email and password on the login page.
3. If you don't have an account, click **Register** and fill in your details. Your admin will assign your role.

### Roles

| Role | Permissions |
|------|------------|
| **Viewer** | Browse documents, search, view enrichments |
| **Analyst** | Viewer + create reports, manage own watch rules |
| **Admin** | Analyst + manage users, sources, and system settings |

### Session

- Your session lasts 30 minutes and auto-refreshes while you're active.
- Click your profile icon in the sidebar to log out.
- If redirected to login, you'll return to your previous page after authenticating.

---

## Dashboard Overview

The dashboard is your home screen, showing:

- **KPI Cards** — Total documents, pending reviews, high-urgency items, reports generated. Trend indicators show daily changes.
- **Activity Chart** — 30-day view of ingested vs. enriched documents.
- **Risk Heatmap** — Regulatory risk scores by region and category.
- **Recent Documents** — Latest documents with status badges and quick links.

The dashboard auto-refreshes every 30 seconds. Use the refresh control in the top-right to adjust or pause.

---

## Searching Regulations

### Basic Search

1. Navigate to the **Search** page from the sidebar.
2. Type your query in the search bar (e.g., "EU AI Act compliance requirements").
3. Press Enter or click Search.

### Search Types

- **Keyword** — Traditional full-text search. Best for exact terms, statute numbers, and case citations.
- **Semantic** — AI-powered meaning-based search. Best for concept queries like "data privacy obligations."
- **Hybrid** (default) — Combines keyword and semantic results for best overall quality.

### Filters

Use the facet panel on the left to narrow results:

- **Jurisdiction** — EU, US-Federal, UK, Canada, APAC, etc.
- **Category** — Privacy, safety, finance, health, etc.
- **Date Range** — Filter by publication date.
- **Urgency Level** — Low, normal, high, critical.

### Tips

- Use quotes for exact phrases: `"algorithmic impact assessment"`
- Results include highlighted snippets showing where your query matched.
- Your recent searches are saved (up to 20) for quick re-access.
- Press **Cmd+K** (Mac) or **Ctrl+K** (Windows) from anywhere to jump to search.

---

## Viewing Documents and Enrichments

### Document List

The **Documents** page shows all ingested regulatory documents. You can:

- Switch between **Table** and **Card** views.
- Sort by date, jurisdiction, or urgency.
- Select multiple documents for bulk report generation.
- Use the filter sidebar to narrow by jurisdiction, status, or urgency.

### Document Detail

Click any document to see its full detail page with AI-enriched analysis:

| Tab | Contents |
|-----|----------|
| **Summary** | AI-generated summary of the document's key points |
| **Key Changes** | Specific regulatory changes and affected parties |
| **Classification** | Domain classification with confidence scores |
| **Impact Matrix** | Region and product category impact scores (1-10) |
| **Draft Response** | AI-generated compliance response draft (copy to clipboard) |

### Status Badges

| Status | Meaning |
|--------|---------|
| **Ingested** | Document received, awaiting AI processing |
| **Processing** | AI agents currently analyzing the document |
| **Enriched** | AI analysis complete, all tabs available |
| **Failed** | Processing error — admin will be notified |

---

## Creating Compliance Reports

### Report Wizard

1. Navigate to **Reports** and click **New Report**.
2. **Step 1 — Select Documents**: Search and select the documents to include. Use the search bar to filter.
3. **Step 2 — Choose Template**: Pick from Standard, Executive, or Detailed templates.
4. **Step 3 — Configure**: Enter a title, select the audience, and choose format (PDF or DOCX).
5. **Step 4 — Review**: Verify your selections and click **Generate Report**.

### Templates

| Template | Best For |
|----------|----------|
| **Standard** | Balanced compliance report with key findings and recommendations |
| **Executive** | High-level summary for leadership with risk scores and action items |
| **Detailed** | Comprehensive analysis with full regulatory text and impact assessments |

### Managing Reports

- **View** — Click the eye icon to preview a report in the browser.
- **Download** — Available for completed reports in PDF or DOCX.
- **Filter** — Use status, template type, and date filters to find reports.
- **Delete** — Remove reports you no longer need.

---

## Setting Up Watch Rules

Watch rules automatically notify you when new documents match your criteria.

### Creating a Rule

1. Go to **Settings > Watch Rules** and click **New Rule**.
2. **Name** your rule (e.g., "EU Privacy Critical Alerts").
3. **Add Conditions** using the visual builder:
   - Select a **Field** (jurisdiction, urgency level, category, status, title).
   - Choose an **Operator** (equals, does not equal, contains, starts with).
   - Enter a **Value**.
   - Add multiple conditions for AND logic.
4. **Select Channels** — Check Email, Slack, and/or In-App.
5. Click **Create Rule**.

### Managing Rules

- **Toggle** the switch to enable/disable a rule without deleting it.
- **Edit** to modify conditions or channels.
- **Delete** with confirmation to permanently remove.

### Notification Preferences

Under **Settings > Notifications**, configure:

- **Channel Toggles** — Enable/disable Email, Slack, In-App globally.
- **Digest Frequency** — Immediate (real-time), Daily (9 AM summary), or Weekly (Monday summary).

---

## Admin: Managing Sources and Users

> These features are only visible to users with the **Admin** role.

### User Management

Under **Settings > Admin**, the user table shows:

- Email, name, role, and status for all users.
- **Deactivate** — Temporarily disable a user account.
- **Change Role** — Promote or demote users (viewer/analyst/admin) with confirmation.

### Regulatory Sources

The sources table shows all configured document ingestion sources:

- Name, URL, status (active/paused/error), and last crawl time.
- **Toggle** to pause or resume crawling.
- Sources crawl at configured intervals (default: 60 minutes).

### System Health

Service status cards show real-time health of:

- Ingestion Service
- Enrichment Service
- Compliance Service
- Notification Service

Each card shows status (healthy/degraded/down) and uptime percentage.
