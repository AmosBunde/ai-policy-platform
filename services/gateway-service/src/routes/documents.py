"""Document management routes - proxies to downstream services."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_documents(page: int = 1, page_size: int = 20, jurisdiction: str = None):
    """List regulatory documents with pagination and filters."""
    return {"message": "Not yet implemented"}


@router.get("/{document_id}")
async def get_document(document_id: str):
    """Get a specific document with its enrichment data."""
    return {"message": "Not yet implemented"}


@router.post("/upload")
async def upload_document():
    """Manually upload a regulatory document."""
    return {"message": "Not yet implemented"}


@router.get("/{document_id}/enrichment")
async def get_enrichment(document_id: str):
    """Get AI enrichment data for a document."""
    return {"message": "Not yet implemented"}
