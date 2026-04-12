"""Redis Pub/Sub event system for cross-service communication."""
import asyncio
import json
import logging
import re
from collections.abc import Callable
from datetime import datetime

import redis.asyncio as aioredis

from shared.config.settings import get_settings

logger = logging.getLogger(__name__)

# Channel names must match this pattern (alphanumeric, dots, hyphens, underscores)
_CHANNEL_PATTERN = re.compile(r"^[a-zA-Z0-9._-]{1,128}$")

ALLOWED_CHANNELS = {
    "document.ingested",
    "document.enriched",
    "document.failed",
    "document.archived",
    "notification.send",
    "report.generated",
}


def _validate_channel(channel: str) -> None:
    """Validate channel name against allowlist pattern."""
    if not _CHANNEL_PATTERN.match(channel):
        raise ValueError(f"Invalid channel name format: {channel!r}")
    if channel not in ALLOWED_CHANNELS:
        raise ValueError(f"Channel not in allowlist: {channel!r}")


def _serialize_event(event) -> str:
    """Serialize an event (Pydantic model or dict) to JSON."""
    if hasattr(event, "model_dump"):
        data = event.model_dump(mode="json")
    else:
        data = dict(event)
        # Convert non-serializable types
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
    return json.dumps(data)


def _deserialize_event(raw: str | bytes) -> dict:
    """Deserialize a JSON event payload."""
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return json.loads(raw)


class RedisEventPublisher:
    """Publish events to Redis Pub/Sub channels."""

    def __init__(self, redis_url: str | None = None):
        settings = get_settings()
        self._url = redis_url or settings.redis_url
        self._redis: aioredis.Redis | None = None

    async def _connect(self, max_retries: int = 5) -> aioredis.Redis:
        """Connect with exponential backoff retry."""
        if self._redis is not None:
            try:
                await self._redis.ping()
                return self._redis
            except Exception:
                self._redis = None

        for attempt in range(1, max_retries + 1):
            try:
                self._redis = aioredis.from_url(self._url, decode_responses=True)
                await self._redis.ping()
                return self._redis
            except Exception as exc:
                if attempt == max_retries:
                    raise ConnectionError(
                        f"Failed to connect to Redis after {max_retries} attempts"
                    ) from exc
                delay = min(2 ** attempt, 30)
                logger.warning(
                    "Redis connection attempt %d/%d failed: %s. Retrying in %ds...",
                    attempt, max_retries, exc, delay,
                )
                await asyncio.sleep(delay)
        raise ConnectionError("Unreachable")

    async def publish(self, channel: str, event) -> int:
        """Publish an event to a channel. Returns number of subscribers that received it."""
        _validate_channel(channel)
        redis = await self._connect()
        payload = _serialize_event(event)
        return await redis.publish(channel, payload)

    async def close(self) -> None:
        if self._redis:
            await self._redis.close()
            self._redis = None


class RedisEventSubscriber:
    """Subscribe to Redis Pub/Sub channels."""

    def __init__(self, redis_url: str | None = None):
        settings = get_settings()
        self._url = redis_url or settings.redis_url
        self._redis: aioredis.Redis | None = None
        self._pubsub: aioredis.client.PubSub | None = None

    async def _connect(self, max_retries: int = 5) -> aioredis.Redis:
        """Connect with exponential backoff retry."""
        if self._redis is not None:
            try:
                await self._redis.ping()
                return self._redis
            except Exception:
                self._redis = None

        for attempt in range(1, max_retries + 1):
            try:
                self._redis = aioredis.from_url(self._url, decode_responses=True)
                await self._redis.ping()
                return self._redis
            except Exception as exc:
                if attempt == max_retries:
                    raise ConnectionError(
                        f"Failed to connect to Redis after {max_retries} attempts"
                    ) from exc
                delay = min(2 ** attempt, 30)
                logger.warning(
                    "Redis connection attempt %d/%d failed: %s. Retrying in %ds...",
                    attempt, max_retries, exc, delay,
                )
                await asyncio.sleep(delay)
        raise ConnectionError("Unreachable")

    async def subscribe(self, channel: str, callback: Callable) -> None:
        """Subscribe to a channel and invoke callback on each message."""
        _validate_channel(channel)
        redis = await self._connect()
        self._pubsub = redis.pubsub()
        await self._pubsub.subscribe(channel)

        async for message in self._pubsub.listen():
            if message["type"] == "message":
                event_data = _deserialize_event(message["data"])
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_data)
                else:
                    callback(event_data)

    async def close(self) -> None:
        if self._pubsub:
            await self._pubsub.unsubscribe()
            await self._pubsub.close()
        if self._redis:
            await self._redis.close()
            self._redis = None
