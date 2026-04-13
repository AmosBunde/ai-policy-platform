"""Tests for compliance routes: auth, ownership, template validation."""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestCreateReport:
    @pytest.mark.asyncio
    async def test_create_report_success(self, client):
        resp = await client.post("/api/v1/reports", json={
            "title": "Q1 Compliance Report",
            "template_id": "standard",
            "document_ids": ["550e8400-e29b-41d4-a716-446655440000"],
            "report_type": "standard",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Q1 Compliance Report"
        assert data["status"] == "completed"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_report_invalid_template_rejected(self, client):
        resp = await client.post("/api/v1/reports", json={
            "title": "Bad Report",
            "template_id": "../../etc/passwd",
            "document_ids": [],
        })
        assert resp.status_code == 400
        assert "Invalid template" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_report_invalid_document_id(self, client):
        resp = await client.post("/api/v1/reports", json={
            "title": "Bad IDs",
            "template_id": "standard",
            "document_ids": ["not-a-uuid"],
        })
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_create_report_executive_summary(self, client):
        resp = await client.post("/api/v1/reports", json={
            "title": "Board Summary",
            "template_id": "executive_summary",
            "document_ids": [],
        })
        assert resp.status_code == 201


class TestListReports:
    @pytest.mark.asyncio
    async def test_list_reports(self, client):
        # Create a report first
        await client.post("/api/v1/reports", json={
            "title": "List Test",
            "template_id": "standard",
            "document_ids": [],
        })
        resp = await client.get("/api/v1/reports")
        assert resp.status_code == 200
        data = resp.json()
        assert "reports" in data
        assert "total" in data


class TestGetReport:
    @pytest.mark.asyncio
    async def test_get_report_success(self, client):
        create_resp = await client.post("/api/v1/reports", json={
            "title": "Get Test",
            "template_id": "standard",
            "document_ids": [],
        })
        report_id = create_resp.json()["id"]

        resp = await client.get(f"/api/v1/reports/{report_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Get Test"

    @pytest.mark.asyncio
    async def test_get_report_not_found(self, client):
        resp = await client.get("/api/v1/reports/550e8400-e29b-41d4-a716-446655440000")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_report_invalid_uuid(self, client):
        resp = await client.get("/api/v1/reports/not-a-uuid")
        assert resp.status_code == 400


class TestDownloadReport:
    @pytest.mark.asyncio
    async def test_download_invalid_format(self, client):
        create_resp = await client.post("/api/v1/reports", json={
            "title": "Download Test",
            "template_id": "standard",
            "document_ids": [],
        })
        report_id = create_resp.json()["id"]

        resp = await client.get(f"/api/v1/reports/{report_id}/download?format=exe")
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_download_not_found(self, client):
        resp = await client.get("/api/v1/reports/550e8400-e29b-41d4-a716-446655440000/download")
        assert resp.status_code == 404


class TestTemplates:
    @pytest.mark.asyncio
    async def test_list_templates(self, client):
        resp = await client.get("/api/v1/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["templates"]) == 3
        template_ids = [t["id"] for t in data["templates"]]
        assert "standard" in template_ids
        assert "executive_summary" in template_ids
        assert "detailed_analysis" in template_ids


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["service"] == "compliance"
