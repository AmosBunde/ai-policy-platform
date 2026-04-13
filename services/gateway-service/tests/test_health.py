"""Tests for Gateway Service health endpoints."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from src.main import app


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "gateway"


@pytest.mark.asyncio
async def test_readiness_check(client):
    response = await client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ready", "degraded")
    assert "services" in data


@pytest.mark.asyncio
async def test_openapi_docs(client):
    response = await client.get("/docs")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_metrics_endpoint(client):
    response = await client.get("/metrics")
    # Prometheus ASGI app may return 200 or redirect
    assert response.status_code in (200, 301, 307)
