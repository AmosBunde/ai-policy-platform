"""Tests for event handler: rule matching, rate limiting."""
import pytest
import time
from src.event_handler import (
    _check_rate_limit,
    _rate_limits,
    _MAX_NOTIFICATIONS_PER_DAY,
)


class TestRateLimiting:
    def setup_method(self):
        """Clear rate limits between tests."""
        _rate_limits.clear()

    def test_allows_under_limit(self):
        assert _check_rate_limit("user1", "email") is True

    def test_blocks_over_limit(self):
        for _ in range(_MAX_NOTIFICATIONS_PER_DAY):
            _check_rate_limit("user2", "email")
        assert _check_rate_limit("user2", "email") is False

    def test_separate_channels(self):
        for _ in range(_MAX_NOTIFICATIONS_PER_DAY):
            _check_rate_limit("user3", "email")
        # Different channel should still be allowed
        assert _check_rate_limit("user3", "slack") is True

    def test_separate_users(self):
        for _ in range(_MAX_NOTIFICATIONS_PER_DAY):
            _check_rate_limit("user4", "email")
        # Different user should still be allowed
        assert _check_rate_limit("user5", "email") is True

    def test_limit_is_50_per_day(self):
        assert _MAX_NOTIFICATIONS_PER_DAY == 50


class TestProcessEnrichedEvent:
    @pytest.mark.asyncio
    async def test_rejects_invalid_uuid(self):
        from src.event_handler import process_enriched_event
        result = await process_enriched_event({"document_id": "invalid"})
        assert result == 0

    @pytest.mark.asyncio
    async def test_handles_empty_event(self):
        from src.event_handler import process_enriched_event
        result = await process_enriched_event({})
        assert result == 0

    @pytest.mark.asyncio
    async def test_valid_uuid_processes(self):
        from src.event_handler import process_enriched_event
        result = await process_enriched_event({
            "document_id": "550e8400-e29b-41d4-a716-446655440000",
            "urgency_level": "high",
        })
        assert isinstance(result, int)
