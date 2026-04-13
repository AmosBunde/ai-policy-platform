"""Tests for Celery tasks."""
import pytest
from unittest.mock import patch, MagicMock


class TestCeleryConfig:
    def test_celery_app_configured(self):
        from src.tasks import celery_app
        assert celery_app.main == "ingestion"
        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.accept_content == ["json"]
        assert celery_app.conf.task_ignore_result is True

    def test_beat_schedule_configured(self):
        from src.tasks import celery_app
        assert "ingest-all-sources" in celery_app.conf.beat_schedule
        schedule = celery_app.conf.beat_schedule["ingest-all-sources"]
        assert schedule["task"] == "ingestion.ingest_all_sources"
        assert schedule["schedule"] == 1800.0

    def test_task_registered(self):
        from src.tasks import ingest_source, ingest_all_sources
        assert ingest_source.name == "ingestion.ingest_source"
        assert ingest_all_sources.name == "ingestion.ingest_all_sources"
