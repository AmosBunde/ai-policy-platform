# Contributing to RegulatorAI

## Table of Contents

1. [Development Setup](#development-setup)
2. [Coding Standards](#coding-standards)
3. [Security Guidelines](#security-guidelines)
4. [Git Workflow](#git-workflow)
5. [PR Process and Review Checklist](#pr-process-and-review-checklist)

---

## Development Setup

### Prerequisites

- Docker Desktop 4.x+ with Docker Compose v2
- Python 3.11+
- Node.js 20 LTS
- Git

### Step-by-Step

```bash
# 1. Fork and clone
git clone https://github.com/your-username/ai-policy-platform.git
cd ai-policy-platform

# 2. Set up environment
cp .env.example .env
# Edit .env with your API keys (OPENAI_API_KEY, JWT_SECRET, etc.)

# 3. Start all services
make up
# Services: http://localhost:3000 (frontend), http://localhost:8000 (API)

# 4. Run database migrations
make migrate

# 5. Seed sample data
make seed

# 6. Verify with tests
make test
```

### Useful Commands

```bash
make up              # Start all services
make down            # Stop all services
make test            # Run all tests (backend + frontend)
make lint            # Lint all code
make logs            # Tail service logs
make logs-service SVC=gateway-service  # Tail specific service
make shell SVC=gateway-service         # Open shell in container
make security-scan   # Run security scans (bandit, npm audit, trivy)
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev          # Start dev server on :3000
npm test             # Run vitest
npm run type-check   # TypeScript check
npm run lint         # ESLint
```

---

## Coding Standards

### Python (Backend Services)

- **Format**: `ruff format` (line length: 120)
- **Lint**: `ruff check`
- **Type check**: `mypy --strict`
- **Docstrings**: Required on all public functions and classes
- **Coverage**: 80% minimum per service
- **Async**: Use `async/await` for all I/O-bound operations
- **Models**: Pydantic v2 for all request/response schemas
- **Queries**: SQLAlchemy ORM only, never raw SQL strings

### TypeScript / React (Frontend)

- **Lint**: ESLint (strict config)
- **Components**: Functional components with TypeScript interfaces for all props
- **State**: Zustand for global state, React Query for server state, `useState` for local
- **Styling**: TailwindCSS utility classes, `clsx` for conditional classes
- **Data fetching**: TanStack Query with custom hooks in `src/hooks/`
- **Forms**: react-hook-form + Zod validation
- **Icons**: lucide-react
- **No `any` types**: Use `unknown` and type narrowing instead

### Shared Conventions

- File naming: `snake_case.py` for Python, `PascalCase.tsx` for components, `camelCase.ts` for hooks/utils
- Max function length: aim for < 50 lines
- Prefer composition over inheritance
- One export per file for components

---

## Security Guidelines

### OWASP Top 10 Awareness

Every contributor should be aware of these common vulnerabilities:

| # | Vulnerability | Our Mitigation |
|---|--------------|----------------|
| A01 | Broken Access Control | RBAC with `require_role()`, admin panel conditionally rendered |
| A02 | Cryptographic Failures | bcrypt (12 rounds), AES-256 at rest, TLS in transit |
| A03 | Injection | Parameterized queries (SQLAlchemy), Pydantic validators, UUID validation |
| A04 | Insecure Design | Defense-in-depth, NetworkPolicy, private subnets |
| A05 | Security Misconfiguration | Pod security contexts, no-new-privileges, read-only filesystems |
| A06 | Vulnerable Components | Dependabot, `npm audit`, `pip-audit`, Trivy scans |
| A07 | Auth Failures | JWT with HS256-only, token revocation, rate limiting on auth |
| A08 | Data Integrity | Content hashing (SHA-256), audit triggers, CloudTrail |
| A09 | Logging Failures | Structured logging, no PII in logs, audit trail on all mutations |
| A10 | SSRF | URL scheme validation, private subnets, no raw URL fetching |

### Input Validation Checklist

Before submitting a PR that handles user input, verify:

- [ ] All text fields have `max_length` constraints in Pydantic models
- [ ] HTML content is sanitized via `sanitize_html()` field validators
- [ ] URL fields enforce `https?://` prefix
- [ ] Path parameters are UUID-validated before database queries
- [ ] Query parameters are bounds-checked (pagination: 1-1000, page_size: 1-100)
- [ ] File uploads are validated for type and size (if applicable)
- [ ] Error responses do not leak internal details (stack traces, SQL errors)

### Secrets

- Never commit secrets, API keys, or credentials
- Use `.env` for local development (`.env` is in `.gitignore`)
- Use Kubernetes Secrets or AWS Secrets Manager in production
- Passwords in API responses: ensure `password_hash` field is excluded from response models

---

## Git Workflow

### Branch Naming

```
feature/{issue-number}-{short-description}
fix/{issue-number}-{short-description}
docs/{description}
```

Examples:
- `feature/015-search-page`
- `fix/042-login-redirect`
- `docs/update-api-reference`

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): subject

body (optional — explain WHY, not WHAT)

footer (optional — "Closes #123")
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Scopes**: `gateway`, `ingestion`, `agents`, `compliance`, `search`, `notifications`, `frontend`, `infra`, `shared`, `docs`

**Examples**:
```
feat(frontend): implement search with autocomplete and facets
fix(gateway): prevent timing attack in login comparison
docs: add security documentation and runbook
test(gateway): add SQL injection security tests
```

### Merge Strategy

All PRs are **squash-merged** to main. The squash commit message should match conventional commit format.

---

## PR Process and Review Checklist

### Before Opening a PR

- [ ] Code compiles / type-checks without errors
- [ ] All existing tests pass (`make test`)
- [ ] New tests added for new functionality
- [ ] Security checklist reviewed (see above)
- [ ] No secrets or credentials in the diff

### PR Template

```markdown
## Summary
Brief description of changes.

## Changes
- Bullet list of what changed

## Test Plan
- [ ] Unit tests added/updated
- [ ] Manual testing steps

## Security
- [ ] Input validation verified
- [ ] No new secrets committed
- [ ] RBAC/auth checked if applicable

Closes #<issue-number>
```

### Review Checklist (for Reviewers)

- [ ] Code is clear and maintainable
- [ ] Tests cover happy path and edge cases
- [ ] No obvious security vulnerabilities (injection, auth bypass, data leaks)
- [ ] API changes are backward-compatible or properly versioned
- [ ] Error handling is appropriate (no swallowed exceptions)
- [ ] No unnecessary dependencies added
- [ ] Performance: no N+1 queries, no unbounded loops
- [ ] Documentation updated if user-facing behavior changed
