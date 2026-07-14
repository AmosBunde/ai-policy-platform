"""Service-to-service authentication tests.

Verifies that internal service routes reject requests without the shared
internal token, accept requests carrying it, and keep health probes open.
"""
import os

import pytest
from fastapi.testclient import TestClient

from shared.config.settings import get_settings
from shared.utils.internal_auth import INTERNAL_TOKEN_HEADER

TEST_TOKEN = "internal-token-that-is-at-least-32-characters-long!"


@pytest.fixture
def client_with_token(monkeypatch):
    monkeypatch.setenv("INTERNAL_SERVICE_TOKEN", TEST_TOKEN)
    monkeypatch.setenv("APP_ENV", "production")
    get_settings.cache_clear()
    from src.main import app

    yield TestClient(app, raise_server_exceptions=False)
    get_settings.cache_clear()


@pytest.fixture
def client_without_token(monkeypatch):
    monkeypatch.delenv("INTERNAL_SERVICE_TOKEN", raising=False)
    monkeypatch.setenv("APP_ENV", "development")
    get_settings.cache_clear()
    from src.main import app

    yield TestClient(app)
    get_settings.cache_clear()


class TestInternalAuth:
    def test_rejects_missing_token(self, client_with_token):
        resp = client_with_token.get("/api/v1/sources")
        assert resp.status_code == 401

    def test_rejects_wrong_token(self, client_with_token):
        resp = client_with_token.get(
            "/api/v1/sources", headers={INTERNAL_TOKEN_HEADER: "wrong-token"}
        )
        assert resp.status_code == 401

    def test_accepts_valid_token(self, client_with_token):
        resp = client_with_token.get(
            "/api/v1/sources", headers={INTERNAL_TOKEN_HEADER: TEST_TOKEN}
        )
        assert resp.status_code == 200

    def test_health_stays_open(self, client_with_token):
        resp = client_with_token.get("/health")
        assert resp.status_code == 200

    def test_unconfigured_token_fails_closed_outside_development(
        self, client_with_token, monkeypatch
    ):
        monkeypatch.setenv("INTERNAL_SERVICE_TOKEN", "")
        get_settings.cache_clear()
        resp = client_with_token.get("/api/v1/sources")
        assert resp.status_code == 503

    def test_development_without_token_allows_with_warning(self, client_without_token):
        resp = client_without_token.get("/api/v1/sources")
        assert resp.status_code == 200

    def test_short_token_is_rejected_at_use(self, client_with_token, monkeypatch):
        monkeypatch.setenv("INTERNAL_SERVICE_TOKEN", "too-short")
        get_settings.cache_clear()
        resp = client_with_token.get("/api/v1/sources")
        # RuntimeError from misconfiguration surfaces as a 500, never silent access
        assert resp.status_code == 500
