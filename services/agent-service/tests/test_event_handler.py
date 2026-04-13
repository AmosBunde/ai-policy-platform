"""Tests for event handler."""
import pytest
from src.event_handler import _validate_uuid


class TestUUIDValidation:
    def test_valid_uuid(self):
        assert _validate_uuid("550e8400-e29b-41d4-a716-446655440000") == "550e8400-e29b-41d4-a716-446655440000"

    def test_invalid_uuid(self):
        with pytest.raises(ValueError, match="Invalid UUID"):
            _validate_uuid("not-a-uuid")

    def test_empty_string(self):
        with pytest.raises(ValueError, match="Invalid UUID"):
            _validate_uuid("")

    def test_sql_injection_attempt(self):
        with pytest.raises(ValueError, match="Invalid UUID"):
            _validate_uuid("'; DROP TABLE documents; --")

    def test_partial_uuid(self):
        with pytest.raises(ValueError, match="Invalid UUID"):
            _validate_uuid("550e8400-e29b-41d4")

    def test_uuid_with_extra_chars(self):
        with pytest.raises(ValueError, match="Invalid UUID"):
            _validate_uuid("550e8400-e29b-41d4-a716-446655440000-extra")


class TestProcessDocumentEvent:
    @pytest.mark.asyncio
    async def test_rejects_invalid_document_id(self):
        from src.event_handler import process_document_event
        # Should log error and return without crashing
        await process_document_event({"document_id": "invalid"})

    @pytest.mark.asyncio
    async def test_handles_missing_document_id(self):
        from src.event_handler import process_document_event
        await process_document_event({})
