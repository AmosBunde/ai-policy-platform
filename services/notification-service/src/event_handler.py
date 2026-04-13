"""Event handler: subscribe to document.enriched, evaluate rules, dispatch notifications."""
import asyncio
import json
import logging
import re
import time
from collections import defaultdict

import redis.asyncio as aioredis

from shared.config.settings import get_settings
from src.rule_engine import evaluate_rule, flatten_enrichment

logger = logging.getLogger(__name__)
settings = get_settings()

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

# Rate limiting: max 50 notifications/day per user per channel
_MAX_NOTIFICATIONS_PER_DAY = 50
# {user_id: {channel: [(timestamp, ...)]}}
_rate_limits: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))


def _check_rate_limit(user_id: str, channel: str) -> bool:
    """Check if user has exceeded notification rate limit for this channel."""
    now = time.time()
    day_ago = now - 86400

    # Clean old entries
    _rate_limits[user_id][channel] = [
        t for t in _rate_limits[user_id][channel] if t > day_ago
    ]

    if len(_rate_limits[user_id][channel]) >= _MAX_NOTIFICATIONS_PER_DAY:
        logger.warning(
            "Rate limit exceeded for user %s on channel %s (%d/day)",
            user_id, channel, _MAX_NOTIFICATIONS_PER_DAY,
        )
        return False

    _rate_limits[user_id][channel].append(now)
    return True


async def dispatch_notification(
    user_id: str,
    user_email: str,
    channel: str,
    rule_name: str,
    document_title: str,
    summary: str,
    urgency_level: str,
    document_id: str | None = None,
    watch_rule_id: str | None = None,
) -> bool:
    """Dispatch a notification through the specified channel with rate limiting."""
    if not _check_rate_limit(user_id, channel):
        return False

    title = f"Regulatory Alert: {document_title[:100]}"

    if channel == "email":
        from src.channels.email import render_email_html, send_email
        html_body = render_email_html(
            title=title,
            document_title=document_title,
            summary=summary,
            urgency_level=urgency_level,
            rule_name=rule_name,
        )
        return await send_email(to=user_email, subject=title, html_body=html_body)

    elif channel == "slack":
        from src.channels.slack import send_slack
        return await send_slack(
            title=title,
            document_title=document_title,
            summary=summary,
            urgency_level=urgency_level,
            rule_name=rule_name,
        )

    elif channel == "inapp":
        from src.channels.inapp import create_notification
        create_notification(
            user_id=user_id,
            watch_rule_id=watch_rule_id,
            document_id=document_id,
            channel="inapp",
            subject=title,
            body=summary[:2000],
        )
        return True

    else:
        logger.warning("Unknown notification channel: %s", channel)
        return False


async def process_enriched_event(event_data: dict) -> int:
    """Process a document.enriched event: evaluate rules, dispatch notifications.

    Returns number of notifications dispatched.
    """
    doc_id = str(event_data.get("document_id", ""))
    if not _UUID_RE.match(doc_id):
        logger.error("Invalid document_id in event: %s", doc_id)
        return 0

    enrichment = event_data.get("enrichment", event_data)
    flat_data = flatten_enrichment(enrichment)
    flat_data["jurisdiction"] = event_data.get("jurisdiction", "")
    flat_data["document_type"] = event_data.get("document_type", "")

    # In production, fetch all active watch rules from DB
    # For now, return 0 as we need the DB to get rules
    logger.info("Processed enriched event for document %s", doc_id)
    return 0


async def start_event_listener() -> None:
    """Subscribe to document.enriched events and process them."""
    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe("document.enriched")

    logger.info("Listening for document.enriched events...")

    async for message in pubsub.listen():
        if message["type"] == "message":
            try:
                event_data = json.loads(message["data"])
                await process_enriched_event(event_data)
            except json.JSONDecodeError:
                logger.error("Invalid JSON in enriched event")
            except Exception as exc:
                logger.error("Error processing enriched event: %s", exc)
