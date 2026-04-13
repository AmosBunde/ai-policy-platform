"""Compliance report routes — proxies to Compliance Service."""
import re

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from shared.config.settings import get_settings
from shared.models.orm import User
from shared.models.schemas import ComplianceReportCreate, ComplianceReportResponse
from src.middleware.auth import get_current_user

router = APIRouter()
settings = get_settings()

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_COMPLIANCE_BASE = f"http://compliance-service:{settings.compliance_port}"


def _validate_uuid(value: str) -> str:
    if not _UUID_RE.match(value):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid report ID format")
    return value


@router.post("/", response_model=ComplianceReportResponse, status_code=201)
async def create_report(
    request: ComplianceReportCreate,
    current_user: User = Depends(get_current_user),
):
    """Generate a new compliance report."""
    payload = request.model_dump(mode="json")
    payload["created_by"] = str(current_user.id)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                f"{_COMPLIANCE_BASE}/api/v1/reports",
                json=payload,
            )
            return resp.json()
        except httpx.RequestError:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Compliance service unavailable")


@router.get("/")
async def list_reports(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
):
    """List all compliance reports."""
    params = {"page": min(max(page, 1), 1000), "page_size": min(max(page_size, 1), 100)}
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(
                f"{_COMPLIANCE_BASE}/api/v1/reports",
                params=params,
            )
            return resp.json()
        except httpx.RequestError:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Compliance service unavailable")


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get a specific compliance report."""
    rid = _validate_uuid(report_id)
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(f"{_COMPLIANCE_BASE}/api/v1/reports/{rid}")
            if resp.status_code == 404:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
            return resp.json()
        except httpx.RequestError:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Compliance service unavailable")


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    format: str = "pdf",
    current_user: User = Depends(get_current_user),
):
    """Download report in specified format."""
    rid = _validate_uuid(report_id)
    safe_format = format[:10] if format else "pdf"
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(
                f"{_COMPLIANCE_BASE}/api/v1/reports/{rid}/download",
                params={"format": safe_format},
            )
            if resp.status_code == 404:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
            return resp.json()
        except httpx.RequestError:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Compliance service unavailable")
