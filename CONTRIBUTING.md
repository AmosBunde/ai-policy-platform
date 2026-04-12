# Contributing to RegulatorAI

## Development Setup

1. Fork and clone the repository
2. Copy `.env.example` to `.env` and fill in values
3. Run `make up` to start all services
4. Run `make test` to verify everything works

## Git Workflow

1. Create a branch: `feature/{issue-number}-{short-description}`
2. Make changes with atomic commits
3. Follow [Conventional Commits](https://www.conventionalcommits.org/): `feat(scope): description`
4. Push and create a PR referencing the issue: `Closes #{number}`
5. All PRs are squash-merged to main

## Coding Standards

### Python
- Format with `ruff format`
- Lint with `ruff check`
- Type check with `mypy --strict`
- Docstrings on all public functions
- 80% minimum test coverage per service

### TypeScript/React
- ESLint + Prettier
- Functional components only
- Props interfaces for all components
- TanStack Query for all API calls
- No `any` types

## Commit Message Format

```
type(scope): subject

body (optional)

footer (optional)
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
Scopes: `gateway`, `ingestion`, `agents`, `compliance`, `search`, `notifications`, `frontend`, `infra`, `shared`, `docs`
