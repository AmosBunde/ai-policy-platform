# RegulatorAI Security Documentation

## Table of Contents

1. [Security Architecture Overview](#security-architecture-overview)
2. [Authentication and Authorization](#authentication-and-authorization)
3. [Data Encryption](#data-encryption)
4. [Input Validation Strategy](#input-validation-strategy)
5. [SSRF and Injection Prevention](#ssrf-and-injection-prevention)
6. [Network Security](#network-security)
7. [Monitoring and Audit](#monitoring-and-audit)
8. [Incident Response](#incident-response)
9. [Responsible Disclosure Policy](#responsible-disclosure-policy)

---

## Security Architecture Overview

RegulatorAI follows a defense-in-depth approach with multiple security layers:

```
Internet
    │
    ▼
┌─────────────────────┐
│   Caddy / Ingress   │  TLS termination, HSTS, rate limiting
│   (Reverse Proxy)   │  Security headers (CSP, X-Frame-Options)
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   Gateway Service   │  JWT auth, RBAC, input validation
│   (API Gateway)     │  Rate limiting (slowapi), request logging
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   Backend Services  │  Parameterized queries (SQLAlchemy ORM)
│   (Private Network) │  Pydantic schema validation, HTML sanitization
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   Data Stores       │  Encryption at rest (KMS), private subnets
│   (Private Subnet)  │  No public access, security group isolation
└─────────────────────┘
```

### Key Principles

- **Least privilege**: All pods run as non-root with read-only filesystems and dropped capabilities.
- **Private by default**: All data stores are in private subnets with no public access.
- **Encrypt everything**: TLS in transit, KMS encryption at rest, bcrypt for passwords.
- **Validate at boundaries**: All user input validated via Pydantic schemas before processing.
- **Audit everything**: VPC flow logs, CloudTrail, structured application logging, database audit triggers.

---

## Authentication and Authorization

### JWT Token Model

- **Access token**: Short-lived (30 minutes), contains `sub` (user ID), `role`, `iat`, `exp`.
- **Refresh token**: Longer-lived (7 days), contains `sub`, `jti` (for revocation), `iat`, `exp`.
- **Algorithm**: HS256 only. Other algorithms are explicitly rejected to prevent algorithm confusion attacks.
- **Secret**: Minimum 32 characters, loaded from environment variable `JWT_SECRET`.

### Password Security

- Hashed with **bcrypt** (12 rounds) — constant-time comparison.
- Strength requirements: 8+ characters, mixed case, at least one digit.
- Login response is identical for "user not found" and "wrong password" to prevent user enumeration.
- Inactive accounts receive the same generic "Invalid credentials" response.

### Role-Based Access Control (RBAC)

| Endpoint | Viewer | Analyst | Admin |
|----------|--------|---------|-------|
| `GET /users/me` | Yes | Yes | Yes |
| `GET /documents/*` | Yes | Yes | Yes |
| `POST /search` | Yes | Yes | Yes |
| `POST /reports` | No | Yes | Yes |
| `GET /users/` (list) | No | No | Yes |
| `PATCH /users/{id}` (role) | No | No | Yes |
| `DELETE /users/{id}` | No | No | Yes |

Non-admin users cannot change roles, active status, or access other users' data.

### Token Revocation

- On logout, refresh tokens are blacklisted in Redis with TTL matching the token's remaining lifetime.
- Revoked tokens are checked during refresh flow.

---

## Data Encryption

### At Rest

| Data Store | Encryption | Key Management |
|-----------|-----------|----------------|
| PostgreSQL (RDS) | AES-256 | AWS KMS (dedicated key, auto-rotation) |
| Redis (ElastiCache) | AES-256 | AWS KMS (dedicated key) |
| OpenSearch | AES-256 | AWS KMS (dedicated key) |
| S3 Backups | AES-256 | AWS KMS (SSE-KMS) |
| CloudTrail Logs | AES-256 | S3 SSE |
| EKS Secrets | Envelope encryption | AWS KMS |

### In Transit

- All external traffic: TLS 1.2+ via Caddy/Ingress with automatic Let's Encrypt certificates.
- HSTS enabled (1 year, includeSubDomains, preload).
- Redis in-transit encryption enabled (TLS).
- OpenSearch node-to-node encryption enabled, TLS 1.2 minimum enforced.
- All inter-service communication within the Kubernetes cluster network.

### Password Storage

- bcrypt with 12 rounds (intentionally slow for brute-force resistance).
- Passwords never logged, never included in API responses.
- `password_hash` field excluded from all Pydantic response models.

---

## Input Validation Strategy

### Pydantic Schema Validation

Every API endpoint uses strict Pydantic models with:

- **Type enforcement**: `strict=True` on sensitive models (login, registration).
- **Max length constraints**: All string fields have explicit `max_length` (e.g., email: 255, password: 128, title: 500, content: 1,000,000).
- **Regex patterns**: Email format validation, search type whitelist (`keyword|semantic|hybrid`).
- **Range constraints**: Page numbers (1-1000), page sizes (1-100), confidence scores (0.0-1.0).

### HTML Sanitization

All user-supplied text fields are sanitized via `sanitize_html()` which strips:

- `<script>`, `<iframe>`, `<object>`, `<embed>`, `<form>`, `<style>`, `<link>`, `<meta>`, `<base>` tags.
- Event handlers (`onclick`, `onerror`, `onload`, etc.).
- `javascript:` URIs.

Sanitization is applied via Pydantic `@field_validator` decorators on `full_name`, `title`, `content`, `summary`, `name` fields.

### UUID Validation

All path parameters that reference entity IDs are validated against a strict UUID regex pattern before database queries, preventing SQL injection via path parameters.

---

## SSRF and Injection Prevention

### SQL Injection

- All database queries use SQLAlchemy ORM with parameterized queries — no raw SQL string concatenation.
- Path parameters are UUID-validated before reaching any query.
- Security tests verify 15+ SQLi payloads are rejected across all endpoints.

### Cross-Site Scripting (XSS)

- Input sanitization strips dangerous HTML tags and event handlers at the Pydantic validation layer.
- Content-Security-Policy header (`default-src 'self'`) restricts script execution.
- X-XSS-Protection, X-Content-Type-Options headers set on all responses.
- Security tests verify 12+ XSS payloads are neutralized.

### Server-Side Request Forgery (SSRF)

- Document URL fields enforce `https?://` prefix via Pydantic validators and database CHECK constraints.
- Non-HTTP schemes (`file://`, `ftp://`, `gopher://`, `data:`) are rejected.
- Network-level controls: data stores in private subnets, security groups restrict egress.

### Path Traversal

- All entity IDs validated as UUIDs — `../` patterns in path parameters return 400.
- File uploads are not stored to local filesystem — documents go directly to database.
- Read-only root filesystems on all pods prevent filesystem writes.

---

## Network Security

### Kubernetes NetworkPolicy

- **Default deny**: All ingress traffic to RegulatorAI pods is denied by default.
- **Gateway-only external**: Only the gateway and dashboard pods accept traffic from the ingress controller.
- **Service isolation**: Backend services (ingestion, agent, compliance, search, notification) only accept traffic from the gateway pod.

### Pod Security

All pods run with:

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop: [ALL]
  seccompProfile:
    type: RuntimeDefault
```

### AWS Infrastructure

- All data stores in **private subnets** with no public IP assignment.
- Security groups: minimal ingress rules (e.g., RDS only accepts port 5432 from EKS security group).
- VPC flow logs enabled for network traffic analysis.
- NAT gateway for outbound internet access from private subnets.

---

## Monitoring and Audit

### Application Logging

- Structured JSON logging via `structlog` on all services.
- Request ID propagated across services for distributed tracing.
- All requests logged: method, path, status code, duration.
- No sensitive data (passwords, tokens, PII) in logs.

### Database Audit

- PostgreSQL audit triggers on all critical tables (users, documents, enrichments, reports, watch rules).
- Captures INSERT/UPDATE/DELETE with old and new values.
- Row-Level Security (RLS) on watch_rules, notification_log, and compliance_reports.

### Infrastructure Audit

- **CloudTrail**: Multi-region trail with log file validation enabled.
- **VPC Flow Logs**: All traffic logged to CloudWatch (90-day retention).
- **EKS Audit Logs**: API, audit, authenticator, controller manager, and scheduler logs enabled.

### Alerting

Prometheus alerts for:

- **ServiceDown**: Service unreachable for >1 minute (CRITICAL).
- **HighErrorRate**: >5% 5xx responses over 5 minutes (WARNING).
- **BruteForceDetected**: >20 auth failures per minute (CRITICAL).
- **HighRateLimitHits**: >10 rate limit hits per second (WARNING).

---

## Incident Response

### Contact

- **Security Team Email**: security@regulatorai.com
- **On-Call PagerDuty**: Integrated via Prometheus Alertmanager
- **Escalation**: CTO and VP Engineering within 30 minutes for critical incidents

### Response Procedure

1. **Detect** — Automated alerts via Prometheus/Grafana or manual report.
2. **Triage** — Classify severity (P1-P4), assign incident commander.
3. **Contain** — Isolate affected systems. See [Runbook](runbook.md) for procedures.
4. **Investigate** — Review logs (CloudTrail, VPC flow logs, application logs).
5. **Remediate** — Apply fixes, rotate compromised credentials.
6. **Communicate** — Notify affected users within 72 hours per GDPR requirements.
7. **Post-mortem** — Document root cause, timeline, and preventive measures.

### Key Rotation Procedures

See [Runbook: Rotate JWT Secret](runbook.md#rotate-jwt-secret) and [Runbook: Rotate API Keys](runbook.md#rotate-api-keys).

---

## Responsible Disclosure Policy

We welcome responsible security research. If you discover a vulnerability:

1. **Do not** exploit the vulnerability beyond what is necessary to confirm it.
2. **Do not** access, modify, or delete other users' data.
3. **Report** the vulnerability to **security@regulatorai.com** with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
   - Suggested remediation (optional)
4. **Response timeline**:
   - Acknowledgment within 48 hours
   - Initial assessment within 5 business days
   - Fix target within 30 days for critical, 90 days for lower severity
5. **Recognition**: We credit researchers in our security advisories (with permission).

### Out of Scope

- Denial-of-service attacks
- Social engineering of employees
- Physical access attacks
- Third-party services not under our control
