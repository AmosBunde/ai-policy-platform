"""Search routes - proxies to Search Service."""
from fastapi import APIRouter

from shared.models.schemas import SearchRequest, SearchResponse

router = APIRouter()


@router.post("/", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """Hybrid search across regulatory documents."""
    return {"message": "Not yet implemented"}


@router.get("/suggest")
async def search_suggestions(q: str):
    """Autocomplete search suggestions."""
    return {"suggestions": []}


@router.get("/facets")
async def get_facets():
    """Get available search facets (jurisdictions, categories, etc.)."""
    return {"facets": {}}
