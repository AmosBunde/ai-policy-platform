"""Tests for database session management."""
import pytest

from shared.utils.database import (
    async_session_factory,
    dispose_engine,
    engine,
    get_db,
    text_query,
)


class TestDatabaseConfiguration:
    def test_engine_pool_size(self):
        assert engine.pool.size() == 10

    def test_engine_max_overflow(self):
        assert engine.pool._max_overflow == 20

    def test_engine_pool_pre_ping(self):
        assert engine.pool._pre_ping is True

    def test_session_factory_configured(self):
        assert async_session_factory is not None

    def test_session_expire_on_commit_disabled(self):
        assert async_session_factory.kw.get("expire_on_commit") is False


class TestGetDb:
    def test_get_db_is_async_generator(self):
        gen = get_db()
        assert hasattr(gen, "__aiter__")
        assert hasattr(gen, "__anext__")


class TestTextQuery:
    def test_text_query_creates_clause(self):
        clause = text_query("SELECT 1")
        assert str(clause) == "SELECT 1"
