"""RegulatorAI Ingestion Service — document crawling, parsing, and ingestion."""

import re
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, Response, UploadFile
from prometheus_client import Counter, Gauge, Histogram, make_asgi_app

from shared.config.settings import get_settings
from shared.utils.errors import register_exception_handlers
from shared.utils.internal_auth import require_internal_token
from shared.utils.logging import RequestIdMiddleware, configure_logging
from src.sources import router as sources_router

settings = get_settings()

configure_logging("ingestion-service", settings.log_level)

# ── Prometheus metrics ────────────────────────────────────
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "path"],
)
docs_ingested_total = Counter(
    "docs_ingested_total",
    "Documents successfully ingested",
)
ingestion_duration_seconds = Histogram(
    "ingestion_duration_seconds",
    "Duration of ingestion operations",
)
ingestion_errors_total = Counter(
    "ingestion_errors_total",
    "Ingestion errors",
    ["error_type"],
)
ingestion_queue_depth = Gauge(
    "ingestion_queue_depth",
    "Number of documents awaiting processing",
)

# ── File upload security ──────────────────────────────────
_ALLOWED_EXTENSIONS = {"pdf", "html", "htm", "txt", "xml"}
_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
_PATH_TRAVERSAL_RE = re.compile(r"(\.\.|/|\\)")


def _validate_filename(filename: str) -> str:
    """Validate filename for path traversal and allowed extensions."""
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    if _PATH_TRAVERSAL_RE.search(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Accepted: {', '.join(sorted(_ALLOWED_EXTENSIONS))}",
        )
    return ext


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="RegulatorAI Ingestion Service",
    version=settings.app_version,
    lifespan=lifespan,
    dependencies=[Depends(require_internal_token)],
)

app.add_middleware(RequestIdMiddleware)
register_exception_handlers(app)


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


# ── Health ────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ingestion"}


# ── Sources & stats (DB-backed) ───────────────────────────
app.include_router(sources_router)


# ── Upload ────────────────────────────────────────────────
@app.post("/api/v1/upload", status_code=201)
async def upload_document(file: UploadFile):
    """Upload a PDF/HTML/TXT/XML document manually."""
    ext = _validate_filename(file.filename)

    # Read with size limit
    contents = await file.read()
    if len(contents) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {_MAX_FILE_SIZE // (1024 * 1024)}MB",
        )

    # Parse based on type
    if ext == "pdf":
        from src.parsers.pdf_parser import parse_pdf

        result = parse_pdf(contents)
    elif ext in ("html", "htm"):
        from src.parsers.html_parser import parse_html

        result = parse_html(contents.decode("utf-8", errors="replace"))
    elif ext in ("txt", "xml"):
        text = contents.decode("utf-8", errors="replace")
        result = {"title": file.filename, "content": text, "metadata": {"format": ext}}
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    from src.parsers.normalizer import normalize

    normalized = normalize(
        title=result.get("title", file.filename),
        content=result.get("content", ""),
        raw_metadata=result.get("metadata", {}),
    )

    docs_ingested_total.inc()
    return {
        "status": "uploaded",
        "content_hash": normalized["content_hash"],
        "title": normalized["title"],
    }


# Stats moved to src/sources.py (DB-backed, mounted via sources_router);
# Prometheus counters remain exposed on /metrics.
