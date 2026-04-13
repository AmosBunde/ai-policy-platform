"""Document management routes — proxies to downstream services."""
import re
import uuid as uuid_mod

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status

from shared.config.settings import get_settings
from shared.models.orm import User
from src.middleware.auth import get_current_user

router = APIRouter()
settings = get_settings()

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

_INGESTION_BASE = f"http://ingestion-service:{settings.ingestion_port}"
_AGENT_BASE = f"http://agent-service:{settings.agent_port}"


def _validate_uuid(value: str) -> str:
    """Validate and sanitize UUID path parameter."""
    if not _UUID_RE.match(value):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document ID format")
    return value


def _safe_headers(token: str) -> dict[str, str]:
    """Build a safe header set for downstream requests — no arbitrary forwarding."""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


@router.get("/")
async def list_documents(
    page: int = 1,
    page_size: int = 20,
    jurisdiction: str | None = None,
    current_user: User = Depends(get_current_user),
):
    """List regulatory documents with pagination and filters."""
    params = {"page": min(max(page, 1), 1000), "page_size": min(max(page_size, 1), 100)}
    if jurisdiction:
        params["jurisdiction"] = jurisdiction[:100]

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(f"{_INGESTION_BASE}/api/v1/documents", params=params)
            return resp.json()
        except httpx.RequestError:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Ingestion service unavailable")


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get a specific document with its enrichment data."""
    doc_id = _validate_uuid(document_id)
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(f"{_INGESTION_BASE}/api/v1/documents/{doc_id}")
            if resp.status_code == 404:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
            return resp.json()
        except httpx.RequestError:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Ingestion service unavailable")


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Manually upload a regulatory document."""
    body = await request.json()
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                f"{_INGESTION_BASE}/api/v1/documents",
                json=body,
            )
            return resp.json()
        except httpx.RequestError:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Ingestion service unavailable")


@router.get("/{document_id}/enrichment")
async def get_enrichment(
    document_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get AI enrichment data for a document."""
    doc_id = _validate_uuid(document_id)
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(f"{_AGENT_BASE}/api/v1/enrichments/{doc_id}")
            if resp.status_code == 404:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrichment not found")
            return resp.json()
        except httpx.RequestError:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Agent service unavailable")
