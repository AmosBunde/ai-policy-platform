"""RegulatorAI Ingestion Service — document crawling and processing."""
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Gauge, Histogram, make_asgi_app

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
ingestion_docs_processed_total = Counter(
    "ingestion_docs_processed_total", "Documents processed by ingestion",
)
ingestion_queue_depth = Gauge(
    "ingestion_queue_depth", "Number of documents awaiting processing",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="RegulatorAI Ingestion Service",
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
    return {"status": "healthy", "service": "ingestion"}
