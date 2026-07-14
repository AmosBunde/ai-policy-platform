"""DB-backed regulatory source management and ingestion statistics."""

import math
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.orm import RegulatoryDocument, RegulatorySource
from shared.models.schemas import SourceType
from shared.utils.database import get_db
from src.crawlers.ssrf_guard import validate_url

router = APIRouter(prefix="/api/v1", tags=["Sources"])


# ── Schemas ───────────────────────────────────────────────


class SourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    source_type: SourceType
    url: str = Field(min_length=1)
    jurisdiction: str | None = Field(default=None, max_length=100)
    category: str | None = Field(default=None, max_length=100)
    crawl_frequency_minutes: int = Field(default=60, ge=5, le=10080)

    @field_validator("url")
    @classmethod
    def url_must_be_safe(cls, value: str) -> str:
        # Same SSRF guard the crawlers enforce at fetch time: block
        # non-http(s) schemes and private/reserved networks at the door.
        return validate_url(value)


class SourceResponse(BaseModel):
    id: uuid.UUID
    name: str
    source_type: str
    url: str
    jurisdiction: str | None
    category: str | None
    crawl_frequency_minutes: int
    is_active: bool
    last_crawled_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Endpoints ─────────────────────────────────────────────


@router.get("/sources")
async def list_sources(
    page: int = 1,
    page_size: int = 20,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """List regulatory sources, newest first, paginated."""
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)

    query = select(RegulatorySource)
    count_query = select(func.count()).select_from(RegulatorySource)
    if active_only:
        query = query.where(RegulatorySource.is_active.is_(True))
        count_query = count_query.where(RegulatorySource.is_active.is_(True))

    total = (await db.execute(count_query)).scalar_one()
    rows = (
        (
            await db.execute(
                query.order_by(RegulatorySource.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .scalars()
        .all()
    )
    return {
        "items": [SourceResponse.model_validate(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": math.ceil(total / page_size) if total else 0,
    }


@router.post("/sources", status_code=status.HTTP_201_CREATED)
async def create_source(
    body: SourceCreate,
    db: AsyncSession = Depends(get_db),
) -> SourceResponse:
    """Register a new regulatory source for crawling."""
    existing = (
        await db.execute(
            select(RegulatorySource).where(RegulatorySource.url == body.url)
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A source with this URL already exists (id={existing.id})",
        )

    source = RegulatorySource(
        name=body.name,
        source_type=body.source_type.value,
        url=body.url,
        jurisdiction=body.jurisdiction,
        category=body.category,
        crawl_frequency_minutes=body.crawl_frequency_minutes,
    )
    db.add(source)
    await db.flush()
    await db.refresh(source)
    return SourceResponse.model_validate(source)


@router.post("/sources/{source_id}/crawl", status_code=status.HTTP_202_ACCEPTED)
async def trigger_crawl(
    source_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Enqueue a manual crawl for a source."""
    source = (
        await db.execute(
            select(RegulatorySource).where(RegulatorySource.id == source_id)
        )
    ).scalar_one_or_none()
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Source not found"
        )
    if not source.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Source is inactive"
        )

    from src.tasks import celery_app

    task = celery_app.send_task("ingestion.ingest_source", args=[str(source_id)])
    return {"source_id": str(source_id), "status": "crawl_queued", "task_id": task.id}


@router.get("/ingestion/stats")
async def ingestion_stats(db: AsyncSession = Depends(get_db)):
    """Real ingestion statistics from the database."""
    total_sources = (
        await db.execute(select(func.count()).select_from(RegulatorySource))
    ).scalar_one()
    active_sources = (
        await db.execute(
            select(func.count())
            .select_from(RegulatorySource)
            .where(RegulatorySource.is_active.is_(True))
        )
    ).scalar_one()
    total_documents = (
        await db.execute(select(func.count()).select_from(RegulatoryDocument))
    ).scalar_one()
    last_crawled_at = (
        await db.execute(select(func.max(RegulatorySource.last_crawled_at)))
    ).scalar_one()

    return {
        "sources": {"total": total_sources, "active": active_sources},
        "documents": {"total": total_documents},
        "last_crawled_at": last_crawled_at,
    }
