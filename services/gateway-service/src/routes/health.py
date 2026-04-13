"""Health check routes."""
import httpx
from fastapi import APIRouter

from shared.config.settings import get_settings

router = APIRouter()
settings = get_settings()

_DOWNSTREAM_SERVICES = {
    "ingestion": f"http://ingestion-service:{settings.ingestion_port}/health",
    "agent": f"http://agent-service:{settings.agent_port}/health",
    "compliance": f"http://compliance-service:{settings.compliance_port}/health",
    "search": f"http://search-service:{settings.search_port}/health",
    "notification": f"http://notification-service:{settings.notification_port}/health",
}


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "gateway"}


@router.get("/health/ready")
async def readiness_check():
    """Check downstream service connectivity with 5s timeout."""
    results = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        for name, url in _DOWNSTREAM_SERVICES.items():
            try:
                resp = await client.get(url)
                results[name] = "healthy" if resp.status_code == 200 else "unhealthy"
            except Exception:
                results[name] = "unreachable"

    all_healthy = all(s == "healthy" for s in results.values())
    return {
        "status": "ready" if all_healthy else "degraded",
        "services": results,
    }
