"""Tests for the DB-backed sources API (list, create, crawl trigger, stats)."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from shared.models.orm import RegulatorySource
from shared.utils.database import get_db
from src.main import app


def _source_row(**overrides):
    row = RegulatorySource(
        id=overrides.get("id", uuid.uuid4()),
        name=overrides.get("name", "EU AI Act feed"),
        source_type=overrides.get("source_type", "rss"),
        url=overrides.get("url", "https://example.com/feed.xml"),
        jurisdiction=overrides.get("jurisdiction", "EU"),
        category=overrides.get("category", "ai"),
        crawl_frequency_minutes=overrides.get("crawl_frequency_minutes", 60),
        is_active=overrides.get("is_active", True),
        last_crawled_at=overrides.get("last_crawled_at"),
        created_at=overrides.get("created_at", datetime.now(timezone.utc)),
    )
    return row


def _result(scalar_one=None, scalar_one_or_none=None, all_rows=None):
    res = MagicMock()
    res.scalar_one.return_value = scalar_one
    res.scalar_one_or_none.return_value = scalar_one_or_none
    res.scalars.return_value.all.return_value = all_rows or []
    return res


@pytest.fixture
def mock_db():
    session = AsyncMock()
    session.add = MagicMock()
    app.dependency_overrides[get_db] = lambda: session
    yield session
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


class TestListSources:
    def test_lists_paginated(self, client, mock_db):
        rows = [_source_row(), _source_row(name="US FTC releases")]
        mock_db.execute.side_effect = [_result(scalar_one=2), _result(all_rows=rows)]
        resp = client.get("/api/v1/sources")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert body["pages"] == 1
        assert len(body["items"]) == 2
        assert body["items"][0]["name"] == "EU AI Act feed"

    def test_clamps_page_size(self, client, mock_db):
        mock_db.execute.side_effect = [_result(scalar_one=0), _result(all_rows=[])]
        resp = client.get("/api/v1/sources?page=-5&page_size=9999")
        assert resp.status_code == 200
        assert resp.json()["page"] == 1
        assert resp.json()["page_size"] == 100


class TestCreateSource:
    def _payload(self, **overrides):
        return {
            "name": "EU AI Act feed",
            "source_type": "rss",
            "url": "https://example.com/feed.xml",
            **overrides,
        }

    def test_creates_source(self, client, mock_db):
        mock_db.execute.side_effect = [_result(scalar_one_or_none=None)]

        async def fake_refresh(obj):
            obj.id = uuid.uuid4()
            obj.is_active = True
            obj.last_crawled_at = None
            obj.created_at = datetime.now(timezone.utc)

        mock_db.refresh.side_effect = fake_refresh
        resp = client.post("/api/v1/sources", json=self._payload())
        assert resp.status_code == 201
        assert resp.json()["url"] == "https://example.com/feed.xml"
        mock_db.add.assert_called_once()

    def test_duplicate_url_conflicts(self, client, mock_db):
        mock_db.execute.side_effect = [_result(scalar_one_or_none=_source_row())]
        resp = client.post("/api/v1/sources", json=self._payload())
        assert resp.status_code == 409

    def test_rejects_ssrf_url(self, client, mock_db):
        resp = client.post(
            "/api/v1/sources", json=self._payload(url="http://169.254.169.254/latest")
        )
        assert resp.status_code == 422

    def test_rejects_file_scheme(self, client, mock_db):
        resp = client.post(
            "/api/v1/sources", json=self._payload(url="file:///etc/passwd")
        )
        assert resp.status_code == 422

    def test_rejects_bad_source_type(self, client, mock_db):
        resp = client.post(
            "/api/v1/sources", json=self._payload(source_type="carrier-pigeon")
        )
        assert resp.status_code == 422


class TestTriggerCrawl:
    def test_enqueues_crawl(self, client, mock_db, monkeypatch):
        source = _source_row()
        mock_db.execute.side_effect = [_result(scalar_one_or_none=source)]

        sent = {}

        def fake_send_task(name, args=None, **kwargs):
            sent["name"], sent["args"] = name, args
            return MagicMock(id="task-abc")

        import src.tasks as tasks_mod

        monkeypatch.setattr(tasks_mod.celery_app, "send_task", fake_send_task)
        resp = client.post(f"/api/v1/sources/{source.id}/crawl")
        assert resp.status_code == 202
        assert resp.json()["task_id"] == "task-abc"
        assert sent["name"] == "ingestion.ingest_source"
        assert sent["args"] == [str(source.id)]

    def test_missing_source_404(self, client, mock_db):
        mock_db.execute.side_effect = [_result(scalar_one_or_none=None)]
        resp = client.post(f"/api/v1/sources/{uuid.uuid4()}/crawl")
        assert resp.status_code == 404

    def test_inactive_source_409(self, client, mock_db):
        mock_db.execute.side_effect = [
            _result(scalar_one_or_none=_source_row(is_active=False))
        ]
        resp = client.post(f"/api/v1/sources/{uuid.uuid4()}/crawl")
        assert resp.status_code == 409

    def test_invalid_uuid_422(self, client, mock_db):
        resp = client.post("/api/v1/sources/not-a-uuid/crawl")
        assert resp.status_code == 422


class TestStats:
    def test_reports_db_counts(self, client, mock_db):
        now = datetime.now(timezone.utc)
        mock_db.execute.side_effect = [
            _result(scalar_one=12),
            _result(scalar_one=9),
            _result(scalar_one=3400),
            _result(scalar_one=now),
        ]
        resp = client.get("/api/v1/ingestion/stats")
        assert resp.status_code == 200
        body = resp.json()
        assert body["sources"] == {"total": 12, "active": 9}
        assert body["documents"]["total"] == 3400
        assert body["last_crawled_at"] is not None
