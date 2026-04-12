"""Tests for security utilities — password hashing, JWT, content hashing, sanitization."""
import os
import uuid
from datetime import timedelta
from unittest.mock import patch

import pytest
from jose import jwt as jose_jwt

# Set a test JWT secret before importing the module
os.environ["JWT_SECRET"] = "test-secret-key-that-is-at-least-32-characters-long!"

# Clear settings cache so JWT_SECRET is picked up
from shared.config.settings import get_settings
get_settings.cache_clear()

from shared.utils.security import (
    _ALLOWED_ALGORITHMS,
    _get_jwt_secret,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_content_hash,
    password_hash,
    password_verify,
    sanitize_input,
    validate_password_strength,
)


class TestPasswordHashing:
    def test_hash_produces_bcrypt_string(self):
        hashed = password_hash("TestPass123")
        assert hashed.startswith("$2b$12$")

    def test_hash_verify_cycle(self):
        password = "MySecurePassword1"
        hashed = password_hash(password)
        assert password_verify(password, hashed)

    def test_wrong_password_fails_verification(self):
        hashed = password_hash("CorrectPassword1")
        assert not password_verify("WrongPassword1", hashed)

    def test_different_passwords_produce_different_hashes(self):
        h1 = password_hash("Password1")
        h2 = password_hash("Password2")
        assert h1 != h2

    def test_same_password_produces_different_hashes_due_to_salt(self):
        h1 = password_hash("SamePass1")
        h2 = password_hash("SamePass1")
        assert h1 != h2  # Different salts


class TestPasswordStrength:
    def test_valid_password(self):
        is_valid, msg = validate_password_strength("SecurePass1")
        assert is_valid is True

    def test_too_short(self):
        is_valid, msg = validate_password_strength("Ab1")
        assert is_valid is False
        assert "8 characters" in msg

    def test_no_lowercase(self):
        is_valid, msg = validate_password_strength("ALLCAPS123")
        assert is_valid is False
        assert "lowercase" in msg

    def test_no_uppercase(self):
        is_valid, msg = validate_password_strength("alllower123")
        assert is_valid is False
        assert "uppercase" in msg

    def test_no_digit(self):
        is_valid, msg = validate_password_strength("NoDigitsHere")
        assert is_valid is False
        assert "digit" in msg

    def test_exactly_8_chars_valid(self):
        is_valid, msg = validate_password_strength("Abcdefg1")
        assert is_valid is True

    def test_empty_password(self):
        is_valid, msg = validate_password_strength("")
        assert is_valid is False


class TestJWTTokens:
    def test_create_and_decode_access_token(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id, "analyst")
        payload = decode_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["role"] == "analyst"
        assert "iat" in payload
        assert "exp" in payload

    def test_create_and_decode_refresh_token(self):
        user_id = uuid.uuid4()
        token = create_refresh_token(user_id)
        payload = decode_token(token)
        assert payload["sub"] == str(user_id)
        assert "jti" in payload
        # jti should be a valid UUID
        uuid.UUID(payload["jti"])

    def test_custom_expiry(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id, "admin", expires_delta=timedelta(hours=2))
        payload = decode_token(token)
        assert payload["exp"] - payload["iat"] == 7200

    def test_expired_token_raises(self):
        user_id = uuid.uuid4()
        token = create_access_token(
            user_id, "analyst", expires_delta=timedelta(seconds=-1)
        )
        with pytest.raises(Exception):
            decode_token(token)

    def test_invalid_token_raises(self):
        with pytest.raises(Exception):
            decode_token("not.a.valid.token")

    def test_tampered_token_raises(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id, "analyst")
        # Tamper with the payload
        parts = token.split(".")
        parts[1] = parts[1] + "x"
        tampered = ".".join(parts)
        with pytest.raises(Exception):
            decode_token(tampered)

    def test_algorithm_whitelist(self):
        assert _ALLOWED_ALGORITHMS == ["HS256"]

    def test_jwt_secret_minimum_length_enforced(self):
        from shared.config.settings import get_settings
        settings = get_settings()
        original = settings.jwt_secret
        try:
            settings.jwt_secret = "short"
            with pytest.raises(RuntimeError, match="at least 32 characters"):
                _get_jwt_secret()
        finally:
            settings.jwt_secret = original

    def test_jwt_secret_empty_raises(self):
        from shared.config.settings import get_settings
        settings = get_settings()
        original = settings.jwt_secret
        try:
            settings.jwt_secret = ""
            with pytest.raises(RuntimeError):
                _get_jwt_secret()
        finally:
            settings.jwt_secret = original


class TestContentHash:
    def test_deterministic(self):
        h1 = generate_content_hash("hello world")
        h2 = generate_content_hash("hello world")
        assert h1 == h2

    def test_different_content_different_hash(self):
        h1 = generate_content_hash("content A")
        h2 = generate_content_hash("content B")
        assert h1 != h2

    def test_produces_64_char_hex(self):
        h = generate_content_hash("test")
        assert len(h) == 64
        int(h, 16)  # Valid hex

    def test_empty_string(self):
        h = generate_content_hash("")
        assert len(h) == 64


class TestInputSanitization:
    def test_strips_script_tags(self):
        result = sanitize_input('<script>alert("xss")</script>Hello')
        assert "<script>" not in result
        assert "alert" not in result
        assert "Hello" in result

    def test_strips_event_handlers(self):
        result = sanitize_input('<img src="x" onerror="alert(1)">')
        assert "onerror" not in result

    def test_strips_javascript_uri(self):
        result = sanitize_input('<a href="javascript:alert(1)">click</a>')
        assert "javascript:" not in result

    def test_strips_iframe(self):
        result = sanitize_input('<iframe src="evil.com"></iframe>Safe text')
        assert "<iframe" not in result
        assert "Safe text" in result

    def test_preserves_safe_markdown(self):
        md = "# Title\n\n**bold** and _italic_ and [link](https://safe.com)"
        result = sanitize_input(md)
        assert "# Title" in result
        assert "**bold**" in result

    def test_preserves_safe_html(self):
        text = "<p>Paragraph</p> <b>bold</b> <i>italic</i>"
        result = sanitize_input(text)
        assert "<p>" in result
        assert "<b>" in result

    def test_mixed_xss_payloads(self):
        payloads = [
            '<script>document.cookie</script>',
            '<img src=x onerror=alert(1)>',
            '<svg onload=alert(1)>',
            '<body onload=alert(1)>',
            'javascript:alert(1)',
            '<SCRIPT>alert(1)</SCRIPT>',
            '<iframe src="data:text/html,<script>alert(1)</script>"></iframe>',
            '<object data="javascript:alert(1)">',
            '<embed src="javascript:alert(1)">',
        ]
        for payload in payloads:
            result = sanitize_input(payload)
            assert "<script" not in result.lower()
            assert "javascript:" not in result.lower()

    def test_empty_string(self):
        assert sanitize_input("") == ""

    def test_plain_text_unchanged(self):
        text = "Just a regular sentence with no HTML."
        assert sanitize_input(text) == text
