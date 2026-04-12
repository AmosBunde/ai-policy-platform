"""Health check routes."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "gateway"}


@router.get("/health/ready")
async def readiness_check():
    # TODO: Check downstream service connectivity
    return {"status": "ready"}
