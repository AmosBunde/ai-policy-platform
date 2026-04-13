"""RegulatorAI Compliance Service — report generation and management."""
import re
import time
import uuid as uuid_mod
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse
from prometheus_client import Counter, Histogram, make_asgi_app

from shared.config.settings import get_settings
from src.generator import VALID_TEMPLATES, render_report, validate_template_id

settings = get_settings()

# Prometheus metrics
http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests",
    ["method", "path", "status"],
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds", "HTTP request duration",
    ["method", "path"],
)
compliance_reports_generated_total = Counter(
    "compliance_reports_generated_total", "Compliance reports generated",
    ["report_type"],
)

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

# In-memory report store (use DB in production)
_reports: dict[str, dict] = {}


def _validate_uuid(value: str) -> str:
    if not _UUID_RE.match(value):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    return value


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="RegulatorAI Compliance Service",
    version=settings.app_version,
    lifespan=lifespan,
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    response: Response = await call_next(request)
    duration = time.perf_counter() - start
    path = request.url.path
    http_requests_total.labels(request.method, path, response.status_code).inc()
    http_request_duration_seconds.labels(request.method, path).observe(duration)
    return response


metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "compliance"}


@app.post("/api/v1/reports", status_code=201)
async def create_report(request: Request):
    """Create a compliance report."""
    body = await request.json()

    title = body.get("title", "Untitled Report")
    template_id = body.get("template_id", "standard")
    document_ids = body.get("document_ids", [])
    report_type = body.get("report_type", "standard")
    created_by = body.get("created_by")

    # Validate template
    try:
        validate_template_id(template_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Validate document_ids are UUIDs
    for doc_id in document_ids:
        if not _UUID_RE.match(str(doc_id)):
            raise HTTPException(status_code=400, detail=f"Invalid document_id: {doc_id}")

    # Build document data (in production, fetch from DB)
    documents = [{"title": f"Document {doc_id}", "enrichment": None} for doc_id in document_ids]

    # Render report HTML
    html_content = render_report(
        template_id=template_id,
        title=title,
        documents=documents,
        report_type=report_type,
        created_by=created_by,
    )

    report_id = str(uuid_mod.uuid4())
    version = 1
    now = datetime.now(timezone.utc).isoformat()

    report = {
        "id": report_id,
        "title": title,
        "template_id": template_id,
        "report_type": report_type,
        "document_ids": document_ids,
        "created_by": created_by,
        "status": "completed",
        "version": version,
        "versions": [{
            "version": version,
            "created_at": now,
            "html_content": html_content,
        }],
        "created_at": now,
        "updated_at": now,
    }

    _reports[report_id] = report
    compliance_reports_generated_total.labels(report_type).inc()

    return {
        "id": report_id,
        "title": title,
        "status": "completed",
        "version": version,
        "created_at": now,
    }


@app.get("/api/v1/reports")
async def list_reports(page: int = 1, page_size: int = 20):
    """List reports (paginated)."""
    all_reports = list(_reports.values())
    start = (page - 1) * min(max(page_size, 1), 100)
    end = start + min(max(page_size, 1), 100)
    paged = all_reports[start:end]

    return {
        "reports": [
            {
                "id": r["id"],
                "title": r["title"],
                "status": r["status"],
                "report_type": r["report_type"],
                "version": r["version"],
                "created_at": r["created_at"],
            }
            for r in paged
        ],
        "total": len(all_reports),
        "page": page,
        "page_size": page_size,
    }


@app.get("/api/v1/reports/{report_id}")
async def get_report(report_id: str):
    """Get a specific report."""
    _validate_uuid(report_id)
    report = _reports.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return {
        "id": report["id"],
        "title": report["title"],
        "status": report["status"],
        "report_type": report["report_type"],
        "template_id": report["template_id"],
        "document_ids": report["document_ids"],
        "version": report["version"],
        "created_at": report["created_at"],
        "updated_at": report["updated_at"],
    }


@app.get("/api/v1/reports/{report_id}/download")
async def download_report(report_id: str, format: str = "pdf"):
    """Download report as PDF or DOCX."""
    _validate_uuid(report_id)
    report = _reports.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if format not in ("pdf", "docx"):
        raise HTTPException(status_code=400, detail="Format must be 'pdf' or 'docx'")

    # Get latest version HTML
    latest_version = report["versions"][-1]
    html_content = latest_version["html_content"]

    if format == "pdf":
        from src.generator import html_to_pdf
        content = html_to_pdf(html_content)
        media_type = "application/pdf"
        filename = f"report-{report_id[:8]}.pdf"
    else:
        from src.generator import html_to_docx
        content = html_to_docx(html_content, title=report["title"])
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"report-{report_id[:8]}.docx"

    import io
    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/v1/templates")
async def list_templates():
    """List available report templates."""
    return {
        "templates": [
            {"id": tid, "name": tid.replace("_", " ").title(), "file": tfile}
            for tid, tfile in VALID_TEMPLATES.items()
        ]
    }
