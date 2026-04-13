"""Search routes — proxies to Search Service."""
import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from shared.config.settings import get_settings
from shared.models.orm import User
from shared.models.schemas import SearchRequest, SearchResponse
from src.middleware.auth import get_current_user

router = APIRouter()
settings = get_settings()

_SEARCH_BASE = f"http://search-service:{settings.search_port}"


@router.post("/", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
):
    """Hybrid search across regulatory documents."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                f"{_SEARCH_BASE}/api/v1/search",
                json=request.model_dump(mode="json"),
            )
            return resp.json()
        except httpx.RequestError:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Search service unavailable")


@router.get("/suggest")
async def search_suggestions(
    q: str,
    current_user: User = Depends(get_current_user),
):
    """Autocomplete search suggestions."""
    safe_q = q[:200].strip()
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(
                f"{_SEARCH_BASE}/api/v1/search/suggest",
                params={"q": safe_q},
            )
            return resp.json()
        except httpx.RequestError:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Search service unavailable")


@router.get("/facets")
async def get_facets(current_user: User = Depends(get_current_user)):
    """Get available search facets."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(f"{_SEARCH_BASE}/api/v1/search/facets")
            return resp.json()
        except httpx.RequestError:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Search service unavailable")
