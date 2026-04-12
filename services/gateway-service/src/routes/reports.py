"""Compliance report routes - proxies to Compliance Service."""
from fastapi import APIRouter

from shared.models.schemas import ComplianceReportCreate, ComplianceReportResponse

router = APIRouter()


@router.post("/", response_model=ComplianceReportResponse, status_code=201)
async def create_report(request: ComplianceReportCreate):
    """Generate a new compliance report."""
    return {"message": "Not yet implemented"}


@router.get("/")
async def list_reports(page: int = 1, page_size: int = 20):
    """List all compliance reports."""
    return {"message": "Not yet implemented"}


@router.get("/{report_id}")
async def get_report(report_id: str):
    """Get a specific compliance report."""
    return {"message": "Not yet implemented"}


@router.get("/{report_id}/download")
async def download_report(report_id: str, format: str = "pdf"):
    """Download report in specified format."""
    return {"message": "Not yet implemented"}
