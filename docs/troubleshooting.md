# Troubleshooting Guide

## Common Issues

### 1. Services Won't Start

**Symptom**: `docker compose up` fails or services exit immediately.

**Checks**:
```bash
# Check service status
docker compose ps

# Check logs for a specific service
docker compose logs gateway-service --tail=50

# Verify .env file exists
ls -la .env
```

**Common causes**:
- Missing `.env` file — copy from `.env.example` and fill in values.
- Port conflicts — another process is using ports 8000, 3000, 5432, 6379, or 9200.
- Docker not running — start Docker Desktop.
- Insufficient memory — Elasticsearch requires at least 2GB. Increase Docker memory allocation.

### 2. Database Connection Errors

**Symptom**: `Connection refused` or `could not connect to server` in logs.

**Checks**:
```bash
# Verify PostgreSQL is healthy
docker compose exec postgres pg_isready -U regulatorai

# Check database exists
docker compose exec postgres psql -U regulatorai -c '\l'
```

**Fixes**:
- Wait 15-30 seconds after startup — services have health check dependencies.
- Run migrations: `docker compose exec gateway-service alembic upgrade head`
- Reset database: `docker compose down -v && docker compose up -d`

### 3. Elasticsearch Fails to Start

**Symptom**: `max virtual memory areas vm.max_map_count [65530] is too low` or OOM killed.

**Fixes**:
```bash
# Linux: increase vm.max_map_count
sudo sysctl -w vm.max_map_count=262144

# Persist across reboots
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf

# macOS (Docker Desktop): increase memory in Docker Desktop > Settings > Resources
```

### 4. Authentication Errors

**Symptom**: `401 Unauthorized` on all API requests.

**Checks**:
- Token expired — access tokens last 30 minutes. Refresh using `/api/v1/auth/refresh`.
- Incorrect `JWT_SECRET` in `.env` — all services must use the same secret.
- Token format — ensure `Authorization: Bearer <token>` header (note the space after "Bearer").

### 5. Search Returns No Results

**Symptom**: Search works but always returns empty results.

**Checks**:
```bash
# Verify Elasticsearch has data
curl -u elastic:${ELASTICSEARCH_PASSWORD} http://localhost:9200/_cat/indices?v

# Check search-service logs
docker compose logs search-service --tail=50
```

**Fixes**:
- Seed data: `docker compose exec gateway-service python -m scripts.seed_data`
- Reindex: See [Runbook: Reindex Elasticsearch](runbook.md#reindex-elasticsearch)

### 6. Frontend Won't Load

**Symptom**: Browser shows blank page or connection refused on `localhost:3000`.

**Checks**:
```bash
# Check dashboard service
docker compose logs dashboard --tail=20

# Verify the service is running
docker compose ps dashboard
```

**Fixes**:
- Clear browser cache and hard refresh (Cmd+Shift+R).
- Check that the API proxy is configured correctly in `vite.config.ts`.
- For development mode: `cd frontend && npm run dev`

### 7. Rate Limiting Blocks Requests

**Symptom**: `429 Too Many Requests` responses.

**Explanation**: The API enforces rate limits per IP address. Login is limited to 10 requests/minute.

**Fixes**:
- Wait for the `Retry-After` header duration.
- In development, rate limits are more permissive. Check `APP_ENV` is set to `development`.

### 8. AI Enrichment Stuck in "Processing"

**Symptom**: Documents stay in "processing" status and never reach "enriched."

**Checks**:
```bash
# Check agent-service logs
docker compose logs agent-service --tail=50

# Check Celery worker
docker compose logs celery-worker --tail=50

# Check Redis connection
docker compose exec redis redis-cli -a ${REDIS_PASSWORD} ping
```

**Common causes**:
- Invalid or missing `OPENAI_API_KEY` in `.env`.
- OpenAI API rate limits — check for 429 errors in agent-service logs.
- Celery worker not running — restart with `docker compose restart celery-worker`.

### 9. Permission Denied (403)

**Symptom**: API returns `403 Forbidden` for endpoints you expect access to.

**Checks**:
- Verify your role: `curl -H "Authorization: Bearer $TOKEN" /api/v1/users/me`
- Admin endpoints (`/users/`, `DELETE /users/{id}`) require the `admin` role.
- Non-admin users can only update their own profile.

### 10. Docker Build Fails

**Symptom**: `docker compose build` fails with dependency errors.

**Fixes**:
```bash
# Clean Docker cache and rebuild
docker compose build --no-cache

# If disk space issues
docker system prune -a

# If network issues downloading packages
docker compose build --build-arg HTTP_PROXY=$HTTP_PROXY
```

---

## Getting Help

1. Check the [Runbook](runbook.md) for operational procedures.
2. Search existing [GitHub Issues](https://github.com/your-org/regulatorai/issues).
3. Open a new issue with logs, steps to reproduce, and environment details.
