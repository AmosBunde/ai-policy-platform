"""RegulatorAI Search Service — Elasticsearch + pgvector hybrid search."""
import re
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response, status
from prometheus_client import Counter, Histogram, make_asgi_app

from shared.config.settings import get_settings
from src.elasticsearch_client import sanitize_query, is_wildcard_only

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
search_queries_total = Counter(
    "search_queries_total", "Total search queries",
    ["search_type"],
)

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="RegulatorAI Search Service",
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
    return {"status": "healthy", "service": "search"}


@app.post("/api/v1/search")
async def search_documents(request: Request):
    """Hybrid search across regulatory documents."""
    body = await request.json()
    query = body.get("query", "")
    search_type = body.get("search_type", "hybrid")

    safe_query = sanitize_query(query)
    if not safe_query:
        raise HTTPException(status_code=400, detail="Query is required")
    if is_wildcard_only(safe_query):
        raise HTTPException(status_code=400, detail="Wildcard-only queries are not allowed")
    if len(safe_query) > 500:
        raise HTTPException(status_code=400, detail="Query exceeds maximum length of 500 characters")

    search_queries_total.labels(search_type).inc()

    from src.elasticsearch_client import ESClient

    jurisdiction = body.get("jurisdiction")
    category = body.get("category")
    urgency_level = body.get("urgency_level")
    date_from = body.get("date_from")
    date_to = body.get("date_to")
    page = body.get("page", 1)
    page_size = body.get("page_size", 20)

    if search_type == "keyword":
        es = ESClient()
        try:
            result = await es.search(
                safe_query, jurisdiction=jurisdiction, category=category,
                urgency_level=urgency_level, date_from=date_from, date_to=date_to,
                page=page, page_size=page_size,
            )
        finally:
            await es.close()

        return {
            "results": result["hits"],
            "total": result["total"],
            "page": page,
            "page_size": page_size,
            "query": safe_query,
        }

    elif search_type == "semantic":
        from src.vector_search import generate_embedding, similarity_search

        query_embedding = await generate_embedding(safe_query)
        sem_results = await similarity_search(query_embedding, top_k=page_size)

        return {
            "results": [
                {
                    "document_id": r["document_id"],
                    "title": "",
                    "snippet": r["chunk_text"][:200],
                    "score": r["similarity"],
                }
                for r in sem_results
            ],
            "total": len(sem_results),
            "page": page,
            "page_size": page_size,
            "query": safe_query,
        }

    else:  # hybrid
        from src.elasticsearch_client import ESClient
        from src.hybrid_search import reciprocal_rank_fusion
        from src.vector_search import generate_embedding, similarity_search

        es = ESClient()
        try:
            es_result = await es.search(
                safe_query, jurisdiction=jurisdiction, category=category,
                urgency_level=urgency_level, date_from=date_from, date_to=date_to,
                page=1, page_size=50,
            )
        finally:
            await es.close()

        query_embedding = await generate_embedding(safe_query)
        sem_results = await similarity_search(query_embedding, top_k=50)

        merged = reciprocal_rank_fusion(es_result["hits"], sem_results)
        start_idx = (page - 1) * page_size
        paged = merged[start_idx:start_idx + page_size]

        return {
            "results": paged,
            "total": len(merged),
            "page": page,
            "page_size": page_size,
            "query": safe_query,
        }


@app.get("/api/v1/search/suggest")
async def search_suggestions(q: str = ""):
    """Autocomplete search suggestions."""
    safe_q = sanitize_query(q)
    if not safe_q:
        return {"suggestions": []}

    from src.elasticsearch_client import ESClient
    es = ESClient()
    try:
        suggestions = await es.suggest(safe_q)
    finally:
        await es.close()

    return {"suggestions": suggestions}


@app.get("/api/v1/search/facets")
async def get_facets():
    """Get available search facets."""
    from src.elasticsearch_client import ESClient
    es = ESClient()
    try:
        facets = await es.get_facets()
    finally:
        await es.close()

    return {"facets": facets}


@app.post("/api/v1/index/{document_id}")
async def index_document_endpoint(document_id: str, request: Request):
    """Index a document (internal service call)."""
    if not _UUID_RE.match(document_id):
        raise HTTPException(status_code=400, detail="Invalid document ID format")

    body = await request.json()

    from src.indexer import index_document
    await index_document(document_id, body)

    return {"status": "indexed", "document_id": document_id}
