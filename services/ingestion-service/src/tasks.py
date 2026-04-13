"""Celery tasks for scheduled document ingestion."""
import asyncio
import json
import logging

from celery import Celery
from celery.schedules import crontab

from shared.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

celery_app = Celery(
    "ingestion",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Don't store task results that might contain sensitive document content
    result_expires=3600,
    task_ignore_result=True,
)


@celery_app.task(name="ingestion.ingest_source", bind=True, max_retries=3)
def ingest_source(self, source_id: str):
    """Crawl a single regulatory source and ingest new documents."""
    logger.info("Starting ingestion for source: %s", source_id)
    try:
        asyncio.run(_ingest_source_async(source_id))
    except Exception as exc:
        logger.error("Ingestion failed for source %s: %s", source_id, exc)
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="ingestion.ingest_all_sources")
def ingest_all_sources():
    """Crawl all active regulatory sources."""
    logger.info("Starting scheduled ingestion of all active sources")
    asyncio.run(_ingest_all_async())


async def _ingest_source_async(source_id: str):
    """Async implementation of source ingestion."""
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from shared.models.orm import RegulatoryDocument, RegulatorySource
    from src.crawlers.rss_crawler import crawl_rss
    from src.crawlers.web_crawler import crawl_web
    from src.parsers.html_parser import parse_html
    from src.parsers.normalizer import generate_content_hash, normalize

    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        result = await session.execute(
            select(RegulatorySource).where(RegulatorySource.id == source_id)
        )
        source = result.scalar_one_or_none()
        if not source:
            logger.error("Source not found: %s", source_id)
            return

        entries = []
        if source.source_type == "rss":
            raw_entries = await crawl_rss(source.url)
            for entry in raw_entries:
                parsed = parse_html(entry.content)
                entries.append(normalize(
                    title=entry.title,
                    content=parsed["content"],
                    url=entry.link,
                    jurisdiction=source.jurisdiction,
                    source_id=str(source.id),
                    external_id=entry.external_id,
                    published_at=entry.published,
                ))
        elif source.source_type in ("crawler", "api"):
            result = await crawl_web(source.url)
            entries.append(normalize(
                title=result["title"],
                content=result["content"],
                url=result["url"],
                jurisdiction=source.jurisdiction,
                source_id=str(source.id),
                raw_metadata=result["metadata"],
            ))

        # Deduplicate and insert
        new_count = 0
        for doc_data in entries:
            existing = await session.execute(
                select(RegulatoryDocument).where(
                    RegulatoryDocument.content_hash == doc_data["content_hash"]
                )
            )
            if existing.scalar_one_or_none() is not None:
                continue

            doc = RegulatoryDocument(**doc_data)
            session.add(doc)
            new_count += 1

        # Update last_crawled_at
        from datetime import datetime, timezone
        source.last_crawled_at = datetime.now(timezone.utc)

        await session.commit()

        # Publish events for new documents
        if new_count > 0:
            try:
                import redis.asyncio as aioredis
                r = aioredis.from_url(settings.redis_url, decode_responses=True)
                await r.publish("document.ingested", json.dumps({
                    "source_id": str(source.id),
                    "new_documents": new_count,
                }))
                await r.close()
            except Exception:
                pass

        logger.info("Ingested %d new documents from source %s", new_count, source_id)

    await engine.dispose()


async def _ingest_all_async():
    """Fetch all active sources and ingest each."""
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from shared.models.orm import RegulatorySource

    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        result = await session.execute(
            select(RegulatorySource).where(RegulatorySource.is_active == True)
        )
        sources = result.scalars().all()

    await engine.dispose()

    for source in sources:
        ingest_source.delay(str(source.id))
        logger.info("Queued ingestion for source: %s (%s)", source.name, source.id)


# Beat schedule: run ingest_all every 30 minutes
celery_app.conf.beat_schedule = {
    "ingest-all-sources": {
        "task": "ingestion.ingest_all_sources",
        "schedule": 1800.0,  # 30 minutes
    },
}
