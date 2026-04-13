"""Event-driven indexer: subscribes to document.enriched, indexes in ES + pgvector."""
import asyncio
import html
import json
import logging
import re

import redis.asyncio as aioredis

from shared.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_DANGEROUS_TAG_RE = re.compile(
    r"<\s*(script|iframe|object|embed|form|style)\b[^>]*>.*?</\s*\1\s*>",
    re.IGNORECASE | re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>")


def sanitize_for_index(text: str) -> str:
    """Sanitize content before indexing to prevent stored XSS in search results."""
    text = _DANGEROUS_TAG_RE.sub("", text)
    text = _TAG_RE.sub("", text)
    return text.strip()


async def index_document(doc_id: str, document_data: dict) -> None:
    """Index a document in Elasticsearch and generate pgvector embeddings."""
    from src.elasticsearch_client import ESClient
    from src.vector_search import generate_embedding, store_embedding

    # Sanitize all text fields before indexing
    es_body = {
        "document_id": doc_id,
        "title": sanitize_for_index(document_data.get("title", "")),
        "content": sanitize_for_index(document_data.get("content", ""))[:100_000],
        "summary": sanitize_for_index(document_data.get("summary", "")),
        "jurisdiction": document_data.get("jurisdiction"),
        "category": document_data.get("category"),
        "document_type": document_data.get("document_type"),
        "urgency_level": document_data.get("urgency_level"),
        "status": document_data.get("status", "enriched"),
        "published_at": document_data.get("published_at"),
        "created_at": document_data.get("created_at"),
        "url": document_data.get("url"),
    }

    # Index in Elasticsearch
    es = ESClient()
    try:
        await es.ensure_index()
        await es.index_document(doc_id, es_body)
        logger.info("Indexed document %s in Elasticsearch", doc_id)
    finally:
        await es.close()

    # Generate and store embeddings
    content = document_data.get("content", "")
    if content:
        try:
            embedding = await generate_embedding(content[:8000])
            from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
            engine = create_async_engine(settings.database_url, echo=False)
            session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            async with session_factory() as session:
                await store_embedding(session, doc_id, 0, content[:2000], embedding)
            await engine.dispose()
            logger.info("Stored embedding for document %s", doc_id)
        except Exception as exc:
            logger.warning("Failed to generate embedding for %s: %s", doc_id, exc)


async def process_enriched_event(event_data: dict) -> None:
    """Process a document.enriched event."""
    doc_id = str(event_data.get("document_id", ""))
    if not _UUID_RE.match(doc_id):
        logger.error("Invalid document_id in enriched event: %s", doc_id)
        return

    logger.info("Processing enriched event for document: %s", doc_id)

    # Fetch full document from DB
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from shared.models.orm import RegulatoryDocument

    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with session_factory() as session:
            result = await session.execute(
                select(RegulatoryDocument).where(RegulatoryDocument.id == doc_id)
            )
            doc = result.scalar_one_or_none()
            if not doc:
                logger.error("Document not found for indexing: %s", doc_id)
                return

            await index_document(doc_id, {
                "title": doc.title,
                "content": doc.content,
                "jurisdiction": doc.jurisdiction,
                "document_type": doc.document_type,
                "status": doc.status,
                "published_at": str(doc.published_at) if doc.published_at else None,
                "created_at": str(doc.created_at) if doc.created_at else None,
                "url": doc.url,
            })
    finally:
        await engine.dispose()


async def start_indexer_listener() -> None:
    """Subscribe to document.enriched and index documents."""
    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe("document.enriched")

    logger.info("Listening for document.enriched events...")

    async for message in pubsub.listen():
        if message["type"] == "message":
            try:
                event_data = json.loads(message["data"])
                await process_enriched_event(event_data)
            except json.JSONDecodeError:
                logger.error("Invalid JSON in enriched event")
            except Exception as exc:
                logger.error("Error processing enriched event: %s", exc)
