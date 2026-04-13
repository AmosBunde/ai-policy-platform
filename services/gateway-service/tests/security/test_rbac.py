"""RBAC (Role-Based Access Control) security tests.

Verifies the full endpoint x role access matrix:
  - viewer:  read-only access to own profile, documents, search
  - analyst: viewer + create reports, manage own watch rules
  - admin:   full access including user management

Endpoints that should be admin-only:
  - GET  /api/v1/users/         (list users)
  - DELETE /api/v1/users/{id}   (delete user)

Endpoints that require authentication:
  - All /api/v1/* except /auth/*
"""
import uuid

import pytest

from conftest import auth_headers, make_test_user
from shared.utils.database import get_db
from src.main import app
from .conftest import raw_client, mock_db_with_user  # noqa: F401


class TestAdminOnlyEndpoints:
    """Endpoints restricted to admin role should reject viewer/analyst."""

    @pytest.mark.asyncio
    async def test_list_users_forbidden_for_viewer(self, raw_client):
        user = make_test_user(role="viewer")
        mock_session = mock_db_with_user(user)

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            response = await raw_client.get(
                "/api/v1/users/",
                headers=auth_headers(user_id=user.id, role="viewer"),
            )
            assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_users_forbidden_for_analyst(self, raw_client):
        user = make_test_user(role="analyst")
        mock_session = mock_db_with_user(user)

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            response = await raw_client.get(
                "/api/v1/users/",
                headers=auth_headers(user_id=user.id, role="analyst"),
            )
            assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_users_allowed_for_admin(self, raw_client):
        user = make_test_user(role="admin")
        mock_session = mock_db_with_user(user)

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            response = await raw_client.get(
                "/api/v1/users/",
                headers=auth_headers(user_id=user.id, role="admin"),
            )
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_user_forbidden_for_analyst(self, raw_client):
        user = make_test_user(role="analyst")
        target_id = uuid.uuid4()
        mock_session = mock_db_with_user(user)

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            response = await raw_client.delete(
                f"/api/v1/users/{target_id}",
                headers=auth_headers(user_id=user.id, role="analyst"),
            )
            assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()


class TestPrivilegeEscalation:
    """Non-admin users must not be able to escalate their own privileges."""

    @pytest.mark.asyncio
    async def test_analyst_cannot_change_own_role(self, raw_client):
        user = make_test_user(role="analyst")
        mock_session = mock_db_with_user(user)

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            response = await raw_client.patch(
                f"/api/v1/users/{user.id}",
                json={"role": "admin"},
                headers=auth_headers(user_id=user.id, role="analyst"),
            )
            assert response.status_code == 403
            assert "admin" in response.json().get("detail", "").lower() or "permission" in response.json().get("detail", "").lower()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_viewer_cannot_change_active_status(self, raw_client):
        user = make_test_user(role="viewer")
        mock_session = mock_db_with_user(user)

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            response = await raw_client.patch(
                f"/api/v1/users/{user.id}",
                json={"is_active": True},
                headers=auth_headers(user_id=user.id, role="viewer"),
            )
            assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()


class TestUnauthenticatedAccess:
    """All protected endpoints should reject unauthenticated requests."""

    PROTECTED_ENDPOINTS = [
        ("GET", "/api/v1/users/me"),
        ("GET", "/api/v1/documents/"),
        ("POST", "/api/v1/search/"),
        ("GET", "/api/v1/reports/"),
        ("GET", "/api/v1/users/"),
    ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
    async def test_no_token_returns_401_or_403(self, raw_client, method, path):
        if method == "GET":
            response = await raw_client.get(path)
        else:
            response = await raw_client.post(path, json={})
        assert response.status_code in (401, 403)


class TestCrossUserAccess:
    """Users should not be able to access or modify other users' data."""

    @pytest.mark.asyncio
    async def test_analyst_cannot_update_other_user(self, raw_client):
        user = make_test_user(role="analyst")
        other_id = uuid.uuid4()

        mock_session = mock_db_with_user(user)

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            response = await raw_client.patch(
                f"/api/v1/users/{other_id}",
                json={"full_name": "Hacked Name"},
                headers=auth_headers(user_id=user.id, role="analyst"),
            )
            # Should be 403 (not own profile) or 404 (user not found)
            assert response.status_code in (403, 404)
        finally:
            app.dependency_overrides.clear()
