"""Semantic search using OpenAI embeddings and pgvector cosine similarity."""
import logging
import re

import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")
_EMBEDDING_DIM = 1536


def sanitize_for_embedding(text_input: str) -> str:
    """Sanitize query text before embedding: strip control characters."""
    return _CONTROL_CHAR_RE.sub("", text_input).strip()


async def generate_embedding(text_input: str, model: str | None = None) -> list[float]:
    """Generate embedding via OpenAI text-embedding-3-small."""
    from openai import AsyncOpenAI

    model = model or settings.openai_embedding_model
    safe_text = sanitize_for_embedding(text_input)
    if not safe_text:
        return [0.0] * _EMBEDDING_DIM

    client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=30.0)
    response = await client.embeddings.create(input=safe_text, model=model)
    return response.data[0].embedding


async def store_embedding(
    session: AsyncSession,
    document_id: str,
    chunk_index: int,
    chunk_text: str,
    embedding: list[float],
) -> None:
    """Store embedding in pgvector."""
    embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
    await session.execute(
        text("""
            INSERT INTO document_embeddings (document_id, chunk_index, chunk_text, embedding)
            VALUES (:doc_id, :chunk_idx, :chunk_text, :embedding::vector)
            ON CONFLICT DO NOTHING
        """),
        {
            "doc_id": document_id,
            "chunk_idx": chunk_index,
            "chunk_text": chunk_text,
            "embedding": embedding_str,
        },
    )
    await session.commit()


async def similarity_search(
    query_embedding: list[float],
    top_k: int = 20,
    db_url: str | None = None,
) -> list[dict]:
    """Cosine similarity search against pgvector. top_k capped at 100."""
    top_k = min(max(top_k, 1), 100)
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    engine = create_async_engine(db_url or settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        result = await session.execute(
            text("""
                SELECT
                    de.document_id,
                    de.chunk_text,
                    de.chunk_index,
                    1 - (de.embedding <=> :query_vec::vector) AS similarity
                FROM document_embeddings de
                ORDER BY de.embedding <=> :query_vec::vector
                LIMIT :top_k
            """),
            {"query_vec": embedding_str, "top_k": top_k},
        )
        rows = result.fetchall()

    await engine.dispose()

    return [
        {
            "document_id": str(row[0]),
            "chunk_text": row[1],
            "chunk_index": row[2],
            "similarity": float(row[3]),
        }
        for row in rows
    ]
