"""Tests for structured logging and secret masking."""
import uuid
from unittest.mock import AsyncMock

import pytest

from shared.utils.logging import (
    _AUTH_PATHS,
    _mask_processor,
    configure_logging,
    mask_secrets,
    RequestIdMiddleware,
)


class TestSecretMasking:
    def test_mask_password_in_json(self):
        text = '{"password": "secret123", "email": "test@example.com"}'
        result = mask_secrets(text)
        assert "secret123" not in result
        assert "***" in result
        assert "test@example.com" in result

    def test_mask_password_equals(self):
        text = "password=mysecret"
        result = mask_secrets(text)
        assert "mysecret" not in result

    def test_mask_token(self):
        text = 'token: "eyJhbGciOiJIUzI1NiJ9.payload.sig"'
        result = mask_secrets(text)
        assert "eyJhbG" not in result

    def test_mask_api_key(self):
        text = 'api_key="sk-1234567890"'
        result = mask_secrets(text)
        assert "sk-1234567890" not in result

    def test_mask_authorization_header(self):
        text = "Authorization: Bearer eyJtoken123"
        result = mask_secrets(text)
        assert "eyJtoken123" not in result

    def test_mask_secret_value(self):
        text = 'secret: "my-jwt-secret-value"'
        result = mask_secrets(text)
        assert "my-jwt-secret-value" not in result

    def test_preserves_non_sensitive_text(self):
        text = "User logged in from 192.168.1.1"
        result = mask_secrets(text)
        assert result == text

    def test_multiple_sensitive_fields(self):
        text = 'password="abc" token="xyz" api_key="key123"'
        result = mask_secrets(text)
        assert "abc" not in result
        assert "xyz" not in result
        assert "key123" not in result

    def test_case_insensitive(self):
        text = 'PASSWORD="secret" Token="value" API_KEY="key"'
        result = mask_secrets(text)
        assert "secret" not in result
        assert "value" not in result
        assert "key" not in result.replace("API_KEY", "")


class TestMaskProcessor:
    def test_masks_event_string(self):
        event_dict = {"event": 'Login with password="secret123"', "level": "info"}
        result = _mask_processor(None, None, event_dict)
        assert "secret123" not in result["event"]

    def test_masks_extra_fields(self):
        event_dict = {
            "event": "auth attempt",
            "auth_header": "Authorization: Bearer mytoken",
            "level": "info",
        }
        result = _mask_processor(None, None, event_dict)
        assert "mytoken" not in result["auth_header"]

    def test_preserves_non_string_values(self):
        event_dict = {"event": "test", "count": 42, "level": "info"}
        result = _mask_processor(None, None, event_dict)
        assert result["count"] == 42


class TestConfigureLogging:
    def test_configure_dev_mode(self):
        configure_logging("test-service", "DEBUG")
        # Should not raise

    def test_configure_prod_mode(self):
        from shared.config.settings import get_settings
        settings = get_settings()
        original = settings.app_env
        try:
            settings.app_env = "production"
            configure_logging("test-service", "WARNING")
        finally:
            settings.app_env = original


class TestAuthPaths:
    def test_auth_paths_defined(self):
        assert "/api/v1/auth/login" in _AUTH_PATHS
        assert "/api/v1/auth/register" in _AUTH_PATHS
        assert "/api/v1/auth/refresh" in _AUTH_PATHS

    def test_non_auth_path_not_in_set(self):
        assert "/api/v1/documents" not in _AUTH_PATHS


class TestRequestIdMiddleware:
    def test_middleware_class_exists(self):
        assert RequestIdMiddleware is not None
