# RegulatorAI Operational Runbook

## Table of Contents

1. [Restart a Service](#restart-a-service)
2. [Clear Cache](#clear-cache)
3. [Reindex Elasticsearch](#reindex-elasticsearch)
4. [Database Backup and Restore](#database-backup-and-restore)
5. [Rotate JWT Secret](#rotate-jwt-secret)
6. [Rotate API Keys](#rotate-api-keys)
7. [Scale Services](#scale-services)
8. [Incident Response Checklist](#incident-response-checklist)

---

## Restart a Service

### Docker Compose

```bash
# Restart a single service
docker compose restart gateway-service

# Restart with rebuild
docker compose up -d --build gateway-service

# Restart all services
docker compose restart
```

### Kubernetes

```bash
# Rolling restart (zero-downtime)
kubectl rollout restart deployment/regulatorai-gateway -n regulatorai

# Check rollout status
kubectl rollout status deployment/regulatorai-gateway -n regulatorai

# Restart all deployments
kubectl get deployments -n regulatorai -o name | xargs -I{} kubectl rollout restart {} -n regulatorai
```

---

## Clear Cache

### Redis Cache Flush

```bash
# Docker Compose
docker compose exec redis redis-cli -a ${REDIS_PASSWORD} FLUSHDB

# Kubernetes
kubectl exec -it $(kubectl get pods -n regulatorai -l app.kubernetes.io/component=redis -o jsonpath='{.items[0].metadata.name}') -n regulatorai -- redis-cli -a ${REDIS_PASSWORD} FLUSHDB
```

### Clear Specific Cache Keys

```bash
# Clear all session caches
docker compose exec redis redis-cli -a ${REDIS_PASSWORD} --scan --pattern 'session:*' | xargs -L 1 docker compose exec -T redis redis-cli -a ${REDIS_PASSWORD} DEL

# Clear rate limit counters
docker compose exec redis redis-cli -a ${REDIS_PASSWORD} --scan --pattern 'rate_limit:*' | xargs -L 1 docker compose exec -T redis redis-cli -a ${REDIS_PASSWORD} DEL
```

**Impact**: Users may need to re-authenticate after a full cache flush.

---

## Reindex Elasticsearch

### Full Reindex

```bash
# Docker Compose
docker compose exec search-service python -c "
from src.indexer import reindex_all
import asyncio
asyncio.run(reindex_all())
"

# Kubernetes
kubectl exec -it $(kubectl get pods -n regulatorai -l app.kubernetes.io/component=search -o jsonpath='{.items[0].metadata.name}') -n regulatorai -- python -c "
from src.indexer import reindex_all
import asyncio
asyncio.run(reindex_all())
"
```

### Delete and Recreate Index

```bash
# Delete the index
curl -X DELETE -u elastic:${ELASTICSEARCH_PASSWORD} http://localhost:9200/regulatory_documents

# Recreate with mappings
curl -X PUT -u elastic:${ELASTICSEARCH_PASSWORD} http://localhost:9200/regulatory_documents -H "Content-Type: application/json" -d @infrastructure/docker/elasticsearch/mappings.json

# Trigger reindex
# (same as above)
```

**Impact**: Search will return incomplete results during reindexing. Allow 5-30 minutes depending on data volume.

---

## Database Backup and Restore

### Manual Backup (Docker Compose)

```bash
# Create a backup
docker compose exec postgres pg_dump \
  -U regulatorai \
  -Fc \
  --no-owner \
  --no-privileges \
  regulatorai > backup-$(date +%Y%m%d-%H%M%S).dump

# Verify backup
pg_restore --list backup-*.dump | head -20
```

### Manual Backup (Kubernetes)

```bash
# Run backup job manually
kubectl create job --from=cronjob/regulatorai-db-backup manual-backup-$(date +%s) -n regulatorai

# Check job status
kubectl get jobs -n regulatorai | grep manual-backup
```

### Restore from Backup

```bash
# Docker Compose — restore to a fresh database
docker compose exec -T postgres pg_restore \
  -U regulatorai \
  -d regulatorai \
  --clean \
  --no-owner \
  --no-privileges \
  < backup-20260413-030000.dump

# Kubernetes — copy backup to pod, then restore
kubectl cp backup.dump regulatorai-postgres-0:/tmp/backup.dump -n regulatorai
kubectl exec regulatorai-postgres-0 -n regulatorai -- pg_restore \
  -U regulatorai_admin \
  -d regulatorai \
  --clean \
  --no-owner \
  /tmp/backup.dump
```

### Automated Backups

- **Production (K8s)**: CronJob runs daily at 3:00 AM UTC. Backups are stored in S3 with AES-256 encryption and 30-day retention.
- **RDS**: Automated backups with 30-day retention, point-in-time recovery enabled.
- **Verify backups**: Check S3 bucket or RDS snapshots weekly.

---

## Rotate JWT Secret

**When**: After a suspected token compromise, or as scheduled rotation (quarterly).

### Procedure

1. **Generate a new secret** (minimum 32 characters):
   ```bash
   openssl rand -base64 48
   ```

2. **Update the secret**:
   ```bash
   # Docker Compose — update .env
   sed -i 's/JWT_SECRET=.*/JWT_SECRET=<new-secret>/' .env

   # Kubernetes — update the secret
   kubectl create secret generic regulatorai-secrets \
     --from-literal=JWT_SECRET=<new-secret> \
     --dry-run=client -o yaml | kubectl apply -n regulatorai -f -
   ```

3. **Rolling restart all services** that use JWT:
   ```bash
   # Docker Compose
   docker compose restart gateway-service ingestion-service agent-service compliance-service search-service notification-service

   # Kubernetes
   kubectl rollout restart deployment -l app.kubernetes.io/name=regulatorai -n regulatorai
   ```

4. **Flush Redis** to invalidate cached sessions:
   ```bash
   docker compose exec redis redis-cli -a ${REDIS_PASSWORD} FLUSHDB
   ```

**Impact**: All existing tokens are immediately invalidated. Users must re-authenticate.

---

## Rotate API Keys

### OpenAI API Key

1. Generate a new key at https://platform.openai.com/api-keys.
2. Update the configuration:
   ```bash
   # Docker Compose
   sed -i 's/OPENAI_API_KEY=.*/OPENAI_API_KEY=<new-key>/' .env
   docker compose restart agent-service

   # Kubernetes
   kubectl create secret generic regulatorai-secrets \
     --from-literal=OPENAI_API_KEY=<new-key> \
     --dry-run=client -o yaml | kubectl apply -n regulatorai -f -
   kubectl rollout restart deployment/regulatorai-agent -n regulatorai
   ```

### Database Password

1. Update password in the database:
   ```sql
   ALTER USER regulatorai_admin WITH PASSWORD 'new_secure_password';
   ```
2. Update connection strings in `.env` or Kubernetes secret.
3. Restart all backend services.

**Impact**: Brief service interruption during restart. Use rolling restarts in Kubernetes for zero-downtime.

---

## Scale Services

### Docker Compose

```bash
# Scale a specific service
docker compose up -d --scale agent-service=4
docker compose up -d --scale search-service=3
```

### Kubernetes (Manual)

```bash
# Scale a deployment
kubectl scale deployment/regulatorai-agent --replicas=4 -n regulatorai
kubectl scale deployment/regulatorai-search --replicas=3 -n regulatorai

# Verify
kubectl get pods -n regulatorai -l app.kubernetes.io/component=agent
```

### Kubernetes (HPA)

HPA is configured for agent-service and search-service:

```bash
# Check current HPA status
kubectl get hpa -n regulatorai

# Adjust HPA limits (edit values-prod.yaml and helm upgrade)
helm upgrade regulatorai infrastructure/kubernetes/helm/regulatorai \
  --namespace regulatorai \
  --values infrastructure/kubernetes/helm/regulatorai/values-prod.yaml \
  --set agent.hpa.maxReplicas=12
```

---

## Incident Response Checklist

### P1 — Service Down / Data Breach

- [ ] **Acknowledge** the alert within 5 minutes
- [ ] **Notify** incident commander and security team
- [ ] **Assess** scope: which services affected? Is data exposed?
- [ ] **Contain**: Isolate affected services, block suspicious IPs
  ```bash
  # Block an IP via network policy
  kubectl annotate ingress regulatorai-ingress \
    nginx.ingress.kubernetes.io/denylist-source-range="<malicious-ip>/32" -n regulatorai
  ```
- [ ] **Preserve evidence**: Capture logs before they rotate
  ```bash
  kubectl logs -l app.kubernetes.io/name=regulatorai --all-containers --since=1h -n regulatorai > incident-logs-$(date +%s).txt
  ```
- [ ] **Remediate**: Apply fix, rotate credentials if compromised
- [ ] **Verify**: Confirm services are restored, run health checks
  ```bash
  curl https://app.regulatorai.com/health
  kubectl get pods -n regulatorai
  ```
- [ ] **Communicate**: Notify affected users within 72 hours (GDPR)
- [ ] **Post-mortem**: Document within 48 hours

### P2 — Degraded Performance

- [ ] Check Grafana dashboards for anomalies
- [ ] Review pod resource usage: `kubectl top pods -n regulatorai`
- [ ] Check for pod restarts: `kubectl get pods -n regulatorai` (RESTARTS column)
- [ ] Scale up if needed (see [Scale Services](#scale-services))
- [ ] Check external dependencies (OpenAI, regulatory sources)

### P3 — Non-Critical Bug / Feature Issue

- [ ] Create GitHub issue with reproduction steps
- [ ] Assign to team member based on affected service
- [ ] Schedule fix for next sprint
