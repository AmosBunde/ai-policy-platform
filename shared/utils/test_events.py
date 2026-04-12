"""Tests for Redis Pub/Sub event system."""
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from shared.utils.events import (
    ALLOWED_CHANNELS,
    _deserialize_event,
    _serialize_event,
    _validate_channel,
    RedisEventPublisher,
)


class TestChannelValidation:
    def test_valid_channels(self):
        for channel in ALLOWED_CHANNELS:
            _validate_channel(channel)  # Should not raise

    def test_invalid_channel_format(self):
        with pytest.raises(ValueError, match="Invalid channel name format"):
            _validate_channel("has spaces")

    def test_channel_not_in_allowlist(self):
        with pytest.raises(ValueError, match="not in allowlist"):
            _validate_channel("unknown.channel")

    def test_empty_channel(self):
        with pytest.raises(ValueError):
            _validate_channel("")

    def test_channel_injection_attempt(self):
        with pytest.raises(ValueError):
            _validate_channel("channel\r\nINJECT")

    def test_long_channel_name(self):
        with pytest.raises(ValueError):
            _validate_channel("a" * 200)


class TestSerialization:
    def test_serialize_dict(self):
        event = {"type": "test", "data": "value"}
        result = _serialize_event(event)
        parsed = json.loads(result)
        assert parsed["type"] == "test"

    def test_serialize_pydantic_model(self):
        from shared.models.schemas import DocumentEvent
        event = DocumentEvent(
            event_type="document.ingested",
            document_id=uuid4(),
            metadata={"source": "test"},
        )
        result = _serialize_event(event)
        parsed = json.loads(result)
        assert parsed["event_type"] == "document.ingested"

    def test_serialize_datetime_iso_format(self):
        now = datetime(2026, 1, 15, 10, 30, 0)
        event = {"timestamp": now, "data": "test"}
        result = _serialize_event(event)
        parsed = json.loads(result)
        assert "2026-01-15" in parsed["timestamp"]

    def test_deserialize_string(self):
        raw = '{"key": "value", "num": 42}'
        result = _deserialize_event(raw)
        assert result["key"] == "value"
        assert result["num"] == 42

    def test_deserialize_bytes(self):
        raw = b'{"key": "value"}'
        result = _deserialize_event(raw)
        assert result["key"] == "value"

    def test_roundtrip(self):
        original = {"event_type": "document.enriched", "id": str(uuid4())}
        serialized = _serialize_event(original)
        deserialized = _deserialize_event(serialized)
        assert deserialized["event_type"] == original["event_type"]
        assert deserialized["id"] == original["id"]


class TestRedisEventPublisher:
    @pytest.mark.asyncio
    async def test_publish_validates_channel(self):
        publisher = RedisEventPublisher(redis_url="redis://localhost:6379")
        with pytest.raises(ValueError, match="not in allowlist"):
            await publisher.publish("bad.channel", {"data": "test"})

    @pytest.mark.asyncio
    async def test_publish_calls_redis(self):
        publisher = RedisEventPublisher(redis_url="redis://localhost:6379")
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        mock_redis.publish = AsyncMock(return_value=1)
        publisher._redis = mock_redis

        result = await publisher.publish("document.ingested", {"data": "test"})
        assert result == 1
        mock_redis.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(self):
        publisher = RedisEventPublisher(redis_url="redis://localhost:6379")
        mock_redis = AsyncMock()
        publisher._redis = mock_redis
        await publisher.close()
        mock_redis.close.assert_called_once()
        assert publisher._redis is None
