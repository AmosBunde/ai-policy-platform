# RegulatorAI API Reference

## Base URL

```
Production:  https://app.regulatorai.com/api/v1
Development: http://localhost:8000/api/v1
```

## Interactive Documentation

The API is fully documented with OpenAPI 3.0:

- **Swagger UI**: `{base_url}/docs`
- **ReDoc**: `{base_url}/redoc`
- **OpenAPI JSON**: `{base_url}/openapi.json`

---

## Authentication

All API endpoints (except `/auth/*`) require a Bearer token.

### Login

```bash
curl -X POST https://app.regulatorai.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "analyst@company.com",
    "password": "YourSecurePassword1"
  }'
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### Register

```bash
curl -X POST https://app.regulatorai.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "new.user@company.com",
    "password": "SecurePass1!",
    "full_name": "Jane Doe"
  }'
```

**Response (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "new.user@company.com",
  "full_name": "Jane Doe",
  "role": "analyst",
  "is_active": true,
  "created_at": "2026-04-13T10:00:00Z",
  "updated_at": "2026-04-13T10:00:00Z"
}
```

### Refresh Token

```bash
curl -X POST https://app.regulatorai.com/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGciOiJIUzI1NiIs..."}'
```

### Logout

```bash
curl -X POST https://app.regulatorai.com/api/v1/auth/logout \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGciOiJIUzI1NiIs..."}'
```

### Using the Token

Include the access token in all subsequent requests:

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  https://app.regulatorai.com/api/v1/users/me
```

---

## Key Endpoints

### Search Documents

```bash
curl -X POST https://app.regulatorai.com/api/v1/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "EU AI Act compliance requirements",
    "search_type": "hybrid",
    "jurisdiction": "EU",
    "page": 1,
    "page_size": 20
  }'
```

**Response (200):**
```json
{
  "results": [
    {
      "document_id": "550e8400-...",
      "title": "EU AI Act - Final Implementation Guidelines",
      "snippet": "Article 6 requires providers of high-risk AI systems to...",
      "score": 0.95,
      "jurisdiction": "EU",
      "published_at": "2024-12-15T00:00:00Z",
      "urgency_level": "critical",
      "highlights": ["<mark>EU AI Act</mark> compliance <mark>requirements</mark>"]
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "query": "EU AI Act compliance requirements"
}
```

### List Documents

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://app.regulatorai.com/api/v1/documents?page=1&page_size=20&jurisdiction=EU"
```

### Get Document Detail

```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://app.regulatorai.com/api/v1/documents/550e8400-e29b-41d4-a716-446655440000
```

### Get Document Enrichment

```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://app.regulatorai.com/api/v1/documents/550e8400-.../enrichment
```

### Create Report

```bash
curl -X POST https://app.regulatorai.com/api/v1/reports \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Q1 2025 EU AI Compliance Report",
    "document_ids": ["550e8400-...", "660e8400-..."],
    "report_type": "executive",
    "template_id": "tpl-executive"
  }'
```

**Response (201):**
```json
{
  "id": "770e8400-...",
  "title": "Q1 2025 EU AI Compliance Report",
  "status": "generating",
  "report_type": "executive",
  "created_at": "2026-04-13T10:30:00Z"
}
```

### List Users (Admin Only)

```bash
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  "https://app.regulatorai.com/api/v1/users?page=1&page_size=20"
```

---

## Rate Limiting

The API enforces rate limits to ensure fair usage:

| Endpoint | Limit | Window |
|----------|-------|--------|
| `POST /auth/login` | 10 requests | per minute |
| `POST /auth/register` | 5 requests | per minute |
| `POST /search` | 60 requests | per minute |
| All other endpoints | 120 requests | per minute |

When rate-limited, the API returns:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 30
```

---

## Error Responses

All errors follow a consistent format:

```json
{
  "detail": "Human-readable error message"
}
```

| Status | Meaning |
|--------|---------|
| 400 | Bad request — invalid input |
| 401 | Unauthorized — invalid or expired token |
| 403 | Forbidden — insufficient permissions |
| 404 | Not found |
| 409 | Conflict — resource already exists |
| 422 | Validation error — check field constraints |
| 429 | Rate limited — retry after the specified delay |
| 502 | Downstream service unavailable |

### Validation Error Detail (422)

```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "String should have at least 8 characters",
      "type": "string_too_short"
    }
  ]
}
```

---

## Password Requirements

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- Maximum 128 characters

---

## Pagination

All list endpoints support pagination:

| Parameter | Default | Max |
|-----------|---------|-----|
| `page` | 1 | 1000 |
| `page_size` | 20 | 100 |

---

## Health Check

```bash
curl https://app.regulatorai.com/health
```

**Response (200):**
```json
{
  "status": "healthy",
  "service": "gateway-service",
  "version": "1.0.0"
}
```

This endpoint does not require authentication and is not rate-limited.
