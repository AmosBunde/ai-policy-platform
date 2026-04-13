"""Tests for user management routes."""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from conftest import auth_headers, make_test_user

from shared.utils.database import get_db
from src.main import app


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _mock_session_returning(*users_in_sequence):
    """Build a mock session that returns different users on successive queries."""
    mock_session = AsyncMock()
    results = []
    for u in users_in_sequence:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = u
        mock_result.scalars.return_value.all.return_value = [u] if u else []
        results.append(mock_result)
    mock_session.execute = AsyncMock(side_effect=results)
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    return mock_session


class TestGetMe:
    @pytest.mark.asyncio
    async def test_get_me(self, client):
        user = make_test_user(email="me@test.com", role="analyst")
        headers = auth_headers(user.id, user.role)
        mock_session = _mock_session_returning(user)

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            resp = await client.get("/api/v1/users/me", headers=headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["email"] == "me@test.com"
            assert "password_hash" not in data
        finally:
            app.dependency_overrides.clear()


class TestUpdateUser:
    @pytest.mark.asyncio
    async def test_admin_can_update_other_user(self, client):
        admin = make_test_user(role="admin", email="admin@test.com")
        target = make_test_user(role="analyst", email="target@test.com")
        headers = auth_headers(admin.id, "admin")

        # First query: get_current_user (admin), Second: get target user
        mock_session = _mock_session_returning(admin, target)

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            resp = await client.patch(
                f"/api/v1/users/{target.id}",
                json={"full_name": "Updated Name"},
                headers=headers,
            )
            assert resp.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_user_can_update_own_profile(self, client):
        user = make_test_user(email="self@test.com")
        headers = auth_headers(user.id, user.role)
        mock_session = _mock_session_returning(user, user)

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            resp = await client.patch(
                f"/api/v1/users/{user.id}",
                json={"full_name": "My New Name"},
                headers=headers,
            )
            assert resp.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_user_cannot_update_other_user(self, client):
        user = make_test_user(role="analyst")
        other_id = uuid.uuid4()
        headers = auth_headers(user.id, "analyst")
        mock_session = _mock_session_returning(user)

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            resp = await client.patch(
                f"/api/v1/users/{other_id}",
                json={"full_name": "Hacked Name"},
                headers=headers,
            )
            assert resp.status_code == 403
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_non_admin_cannot_change_role(self, client):
        user = make_test_user(role="analyst")
        headers = auth_headers(user.id, "analyst")
        mock_session = _mock_session_returning(user, user)

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            resp = await client.patch(
                f"/api/v1/users/{user.id}",
                json={"role": "admin"},
                headers=headers,
            )
            assert resp.status_code == 403
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_invalid_uuid_rejected(self, client):
        user = make_test_user()
        headers = auth_headers(user.id, user.role)
        mock_session = _mock_session_returning(user)

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            resp = await client.patch(
                "/api/v1/users/not-a-uuid",
                json={"full_name": "Test"},
                headers=headers,
            )
            assert resp.status_code == 400
        finally:
            app.dependency_overrides.clear()


class TestDeleteUser:
    @pytest.mark.asyncio
    async def test_admin_can_delete_user(self, client):
        admin = make_test_user(role="admin", email="admin@test.com")
        target = make_test_user(role="analyst", email="target@test.com")
        headers = auth_headers(admin.id, "admin")

        # require_role -> get_current_user (query 1), then delete query (query 2)
        mock_session = _mock_session_returning(admin, target)

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            resp = await client.delete(
                f"/api/v1/users/{target.id}",
                headers=headers,
            )
            assert resp.status_code == 204
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_admin_cannot_delete_self(self, client):
        admin = make_test_user(role="admin")
        headers = auth_headers(admin.id, "admin")
        mock_session = _mock_session_returning(admin)

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            resp = await client.delete(
                f"/api/v1/users/{admin.id}",
                headers=headers,
            )
            assert resp.status_code == 400
            assert "own account" in resp.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_analyst_cannot_delete_users(self, client):
        analyst = make_test_user(role="analyst")
        other_id = uuid.uuid4()
        headers = auth_headers(analyst.id, "analyst")
        mock_session = _mock_session_returning(analyst)

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            resp = await client.delete(
                f"/api/v1/users/{other_id}",
                headers=headers,
            )
            assert resp.status_code == 403
        finally:
            app.dependency_overrides.clear()
