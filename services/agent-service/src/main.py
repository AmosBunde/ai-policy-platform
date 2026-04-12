"""RegulatorAI Agent Service — LangGraph multi-agent orchestration."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared.config.settings import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="RegulatorAI Agent Service",
    version=settings.app_version,
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "agent"}


@app.post("/api/v1/analyze/{document_id}")
async def analyze_document(document_id: str):
    """Trigger LangGraph analysis pipeline for a document."""
    # TODO: Import and invoke the LangGraph pipeline
    return {"document_id": document_id, "status": "queued"}


@app.get("/api/v1/analyze/{document_id}/status")
async def analysis_status(document_id: str):
    """Check analysis pipeline status."""
    return {"document_id": document_id, "status": "pending"}
