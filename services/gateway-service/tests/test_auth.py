"""Tests for authentication endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_login_endpoint_exists(client):
    response = await client.post("/api/v1/auth/login", json={
        "email": "test@test.com",
        "password": "testpassword"
    })
    # Should return 501 (not implemented) not 404
    assert response.status_code == 501


@pytest.mark.asyncio
async def test_register_endpoint_exists(client):
    response = await client.post("/api/v1/auth/register", json={
        "email": "new@test.com",
        "password": "testpassword",
        "full_name": "Test User",
        "role": "analyst"
    })
    assert response.status_code == 501


@pytest.mark.asyncio
async def test_logout_endpoint(client):
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_login_validation_email_required(client):
    response = await client.post("/api/v1/auth/login", json={
        "password": "testpassword"
    })
    assert response.status_code == 422
