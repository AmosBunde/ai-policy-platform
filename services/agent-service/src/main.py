"""RegulatorAI Agent Service — LangGraph multi-agent orchestration."""
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Histogram, make_asgi_app

from shared.config.settings import get_settings

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
agent_documents_processed_total = Counter(
    "agent_documents_processed_total", "Documents analyzed by agent pipeline",
)
agent_processing_duration_seconds = Histogram(
    "agent_processing_duration_seconds", "Time to process a document through the pipeline",
)
agent_node_duration_seconds = Histogram(
    "agent_node_duration_seconds", "Duration per pipeline node",
    ["node"],
)
llm_tokens_total = Counter(
    "llm_tokens_total", "Total LLM tokens consumed",
    ["model"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="RegulatorAI Agent Service",
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
    return {"status": "healthy", "service": "agent"}


@app.post("/api/v1/analyze/{document_id}")
async def analyze_document(document_id: str):
    """Trigger LangGraph analysis pipeline for a document."""
    return {"document_id": document_id, "status": "queued"}


@app.get("/api/v1/analyze/{document_id}/status")
async def analysis_status(document_id: str):
    """Check analysis pipeline status."""
    return {"document_id": document_id, "status": "pending"}
