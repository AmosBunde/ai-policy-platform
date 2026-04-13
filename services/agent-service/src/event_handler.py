"""Redis event handler: subscribe to document.ingested, trigger pipeline."""
import asyncio
import json
import logging
import re
import uuid

import redis.asyncio as aioredis

from shared.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def _validate_uuid(value: str) -> str:
    """Validate document_id from event is a valid UUID."""
    if not _UUID_RE.match(value):
        raise ValueError(f"Invalid UUID in event: {value!r}")
    return value


async def process_document_event(event_data: dict) -> None:
    """Process a document.ingested event: fetch document, run pipeline, publish result."""
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from shared.models.orm import DocumentEnrichment, RegulatoryDocument
    from src.pipeline import run_pipeline

    doc_id_raw = event_data.get("document_id", "")
    try:
        doc_id = _validate_uuid(str(doc_id_raw))
    except ValueError as exc:
        logger.error("Invalid document_id in event: %s", exc)
        return

    logger.info("Processing document: %s", doc_id)

    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with session_factory() as session:
            result = await session.execute(
                select(RegulatoryDocument).where(RegulatoryDocument.id == doc_id)
            )
            document = result.scalar_one_or_none()
            if document is None:
                logger.error("Document not found: %s", doc_id)
                return

            # Update status to processing
            document.status = "processing"
            await session.commit()

            try:
                enrichment_data = await run_pipeline(
                    document_id=str(document.id),
                    content=document.content,
                    metadata={
                        "title": document.title,
                        "jurisdiction": document.jurisdiction,
                        "document_type": document.document_type,
                    },
                )

                # Persist enrichment
                enrichment = DocumentEnrichment(
                    document_id=document.id,
                    **enrichment_data,
                )
                session.add(enrichment)
                document.status = "enriched"
                await session.commit()

                # Publish success event
                await _publish_event("document.enriched", {
                    "document_id": str(document.id),
                    "urgency_level": enrichment_data.get("urgency_level", "normal"),
                })

                logger.info("Document enriched: %s", doc_id)

            except Exception as exc:
                document.status = "failed"
                await session.commit()

                await _publish_event("document.failed", {
                    "document_id": str(document.id),
                    "error": str(exc)[:500],
                })

                logger.error("Pipeline failed for document %s: %s", doc_id, exc)

    finally:
        await engine.dispose()


async def _publish_event(channel: str, data: dict) -> None:
    """Publish event to Redis."""
    try:
        r = aioredis.from_url(settings.redis_url, decode_responses=True)
        await r.publish(channel, json.dumps(data))
        await r.close()
    except Exception as exc:
        logger.warning("Failed to publish event to %s: %s", channel, exc)


async def start_event_listener() -> None:
    """Subscribe to document.ingested and process events."""
    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe("document.ingested")

    logger.info("Listening for document.ingested events...")

    async for message in pubsub.listen():
        if message["type"] == "message":
            try:
                event_data = json.loads(message["data"])
                await process_document_event(event_data)
            except json.JSONDecodeError:
                logger.error("Invalid JSON in event message")
            except Exception as exc:
                logger.error("Error processing event: %s", exc)
