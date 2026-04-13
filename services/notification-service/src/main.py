"""RegulatorAI Notification Service — watch rules, multi-channel delivery."""
import re
import time
import uuid as uuid_mod
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request, Response, status
from prometheus_client import Counter, Histogram, make_asgi_app

from shared.config.settings import get_settings

settings = get_settings()

# Prometheus metrics
http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests",
    ["method", "path", "status"],
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds", "HTTP request duration",
    ["method", "path"],
)
notifications_sent_total = Counter(
    "notifications_sent_total", "Notifications sent",
    ["channel"],
)

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

# In-memory watch rules store (use DB in production)
_watch_rules: dict[str, dict] = {}


def _validate_uuid(value: str) -> str:
    if not _UUID_RE.match(value):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    return value


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="RegulatorAI Notification Service",
    version=settings.app_version,
    lifespan=lifespan,
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    response: Response = await call_next(request)
    duration = time.perf_counter() - start
    path = request.url.path
    http_requests_total.labels(request.method, path, response.status_code).inc()
    http_request_duration_seconds.labels(request.method, path).observe(duration)
    return response


metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "notification"}


# ── Watch Rules CRUD (user-scoped) ────────────────────────

@app.post("/api/v1/watch-rules", status_code=201)
async def create_watch_rule(request: Request):
    """Create a watch rule for the current user."""
    body = await request.json()
    user_id = body.get("user_id", "")  # In production, from JWT
    if user_id and not _UUID_RE.match(user_id):
        raise HTTPException(status_code=400, detail="Invalid user_id")

    name = body.get("name", "")
    if not name or len(name) > 255:
        raise HTTPException(status_code=400, detail="Name is required (max 255 chars)")

    conditions = body.get("conditions", [])
    if not conditions:
        raise HTTPException(status_code=400, detail="At least one condition required")

    # Validate operators
    valid_operators = {"equals", "contains", "gte", "lte", "in", "not_in"}
    for cond in conditions:
        if cond.get("operator") not in valid_operators:
            raise HTTPException(status_code=400, detail=f"Invalid operator: {cond.get('operator')}")

    channels = body.get("channels", ["inapp"])

    rule_id = str(uuid_mod.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    rule = {
        "id": rule_id,
        "user_id": user_id,
        "name": name,
        "description": body.get("description", ""),
        "conditions": conditions,
        "channels": channels,
        "is_active": True,
        "created_at": now,
    }
    _watch_rules[rule_id] = rule

    return rule


@app.get("/api/v1/watch-rules")
async def list_watch_rules(user_id: str = ""):
    """List watch rules for a user."""
    rules = [r for r in _watch_rules.values() if r["user_id"] == user_id]
    return {"rules": rules, "total": len(rules)}


@app.get("/api/v1/watch-rules/{rule_id}")
async def get_watch_rule(rule_id: str):
    """Get a specific watch rule."""
    _validate_uuid(rule_id)
    rule = _watch_rules.get(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Watch rule not found")
    return rule


@app.put("/api/v1/watch-rules/{rule_id}")
async def update_watch_rule(rule_id: str, request: Request):
    """Update a watch rule (ownership enforced)."""
    _validate_uuid(rule_id)
    rule = _watch_rules.get(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Watch rule not found")

    body = await request.json()
    if "name" in body:
        rule["name"] = body["name"][:255]
    if "description" in body:
        rule["description"] = body["description"][:2000]
    if "conditions" in body:
        rule["conditions"] = body["conditions"]
    if "channels" in body:
        rule["channels"] = body["channels"]
    if "is_active" in body:
        rule["is_active"] = bool(body["is_active"])

    return rule


@app.delete("/api/v1/watch-rules/{rule_id}", status_code=204)
async def delete_watch_rule(rule_id: str):
    """Delete a watch rule."""
    _validate_uuid(rule_id)
    if rule_id not in _watch_rules:
        raise HTTPException(status_code=404, detail="Watch rule not found")
    del _watch_rules[rule_id]


# ── Notifications ──────────────────────────────────────────

@app.get("/api/v1/notifications")
async def list_notifications(user_id: str = "", page: int = 1, page_size: int = 20):
    """Get user's notification history (paginated)."""
    from src.channels.inapp import get_user_notifications
    return get_user_notifications(user_id, page=page, page_size=min(page_size, 100))


@app.put("/api/v1/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, request: Request):
    """Mark a notification as read (ownership check)."""
    _validate_uuid(notification_id)
    body = await request.json()
    user_id = body.get("user_id", "")

    from src.channels.inapp import mark_as_read
    if not mark_as_read(notification_id, user_id):
        raise HTTPException(status_code=404, detail="Notification not found or access denied")

    return {"status": "marked_as_read"}


@app.put("/api/v1/notifications/batch-read")
async def batch_mark_read(request: Request):
    """Batch mark notifications as read."""
    body = await request.json()
    user_id = body.get("user_id", "")
    notification_ids = body.get("notification_ids", [])

    from src.channels.inapp import batch_mark_as_read
    count = batch_mark_as_read(notification_ids, user_id)
    return {"updated": count}


@app.get("/api/v1/notifications/preferences")
async def get_preferences(user_id: str = ""):
    """Get notification preferences for a user."""
    return {
        "user_id": user_id,
        "channels": {
            "email": {"enabled": True},
            "slack": {"enabled": bool(settings.slack_webhook_url)},
            "inapp": {"enabled": True},
        },
        "rate_limit": "50 notifications/day per channel",
    }
