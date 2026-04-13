"""JWT authentication security tests.

Verifies:
  - Invalid JWTs are rejected
  - Expired JWTs are rejected
  - Tampered JWTs are rejected
  - Algorithm confusion attacks are blocked (only HS256 accepted)
  - Tokens with missing claims are rejected
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from .conftest import client  # noqa: F401


JWT_SECRET = "test-secret-key-that-is-at-least-32-characters-long-for-testing!"


def _make_token(payload: dict, secret: str = JWT_SECRET, algorithm: str = "HS256") -> str:
    return jwt.encode(payload, secret, algorithm=algorithm)


def _valid_payload(user_id: str | None = None, role: str = "analyst") -> dict:
    now = datetime.now(timezone.utc)
    return {
        "sub": user_id or str(uuid.uuid4()),
        "role": role,
        "iat": now,
        "exp": now + timedelta(hours=1),
    }


class TestInvalidJWT:
    """Invalid JWT tokens should be rejected with 401/403."""

    @pytest.mark.asyncio
    async def test_completely_invalid_token(self, client):
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer not-a-real-jwt"},
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_empty_bearer_token(self, client):
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer "},
        )
        assert response.status_code in (401, 403, 422)

    @pytest.mark.asyncio
    async def test_missing_bearer_prefix(self, client):
        token = _make_token(_valid_payload())
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": token},
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_malformed_jwt_segments(self, client):
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer aaa.bbb"},
        )
        assert response.status_code in (401, 403)


class TestExpiredJWT:
    """Expired JWT tokens should be rejected."""

    @pytest.mark.asyncio
    async def test_expired_token_rejected(self, client):
        payload = _valid_payload()
        payload["exp"] = datetime.now(timezone.utc) - timedelta(hours=1)
        payload["iat"] = datetime.now(timezone.utc) - timedelta(hours=2)
        token = _make_token(payload)

        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_expired_by_one_second(self, client):
        """Even tokens expired by 1 second should be rejected."""
        payload = _valid_payload()
        payload["exp"] = datetime.now(timezone.utc) - timedelta(seconds=1)
        token = _make_token(payload)

        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401


class TestTamperedJWT:
    """JWT tokens signed with wrong secret should be rejected."""

    @pytest.mark.asyncio
    async def test_wrong_secret(self, client):
        token = _make_token(_valid_payload(), secret="wrong-secret-key-32-characters-long-xxxx")

        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_modified_payload(self, client):
        """Token with payload modified after signing should be rejected."""
        # Create valid token, then modify a character in the payload segment
        token = _make_token(_valid_payload())
        parts = token.split(".")
        # Flip a character in the payload
        payload_b64 = list(parts[1])
        payload_b64[5] = "X" if payload_b64[5] != "X" else "Y"
        parts[1] = "".join(payload_b64)
        tampered = ".".join(parts)

        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {tampered}"},
        )
        assert response.status_code == 401


class TestAlgorithmConfusion:
    """Algorithm confusion attacks — only HS256 should be accepted."""

    @pytest.mark.asyncio
    async def test_none_algorithm_rejected(self, client):
        """'none' algorithm bypass attempt should be rejected."""
        payload = _valid_payload()
        # Manually construct a token with alg=none
        import base64
        import json

        header = base64.urlsafe_b64encode(
            json.dumps({"alg": "none", "typ": "JWT"}).encode()
        ).rstrip(b"=").decode()
        body = base64.urlsafe_b64encode(
            json.dumps(payload, default=str).encode()
        ).rstrip(b"=").decode()
        fake_token = f"{header}.{body}."

        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_hs384_rejected(self, client):
        """HS384 algorithm should be rejected (only HS256 is allowed)."""
        token = _make_token(_valid_payload(), algorithm="HS384")

        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_hs512_rejected(self, client):
        """HS512 algorithm should be rejected."""
        token = _make_token(_valid_payload(), algorithm="HS512")

        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401


class TestMissingClaims:
    """Tokens missing required claims should be rejected."""

    @pytest.mark.asyncio
    async def test_missing_sub_claim(self, client):
        now = datetime.now(timezone.utc)
        payload = {"role": "analyst", "iat": now, "exp": now + timedelta(hours=1)}
        token = _make_token(payload)

        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_sub_not_uuid(self, client):
        payload = _valid_payload()
        payload["sub"] = "not-a-uuid"
        token = _make_token(payload)

        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
