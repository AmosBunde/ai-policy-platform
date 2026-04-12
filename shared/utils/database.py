"""Async database session factory with connection pooling for FastAPI."""
import asyncio
import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from shared.config.settings import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=(settings.app_env == "development"),
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def wait_for_db(max_retries: int = 5, retry_delay: float = 2.0) -> None:
    """Retry connecting to the database on startup."""
    for attempt in range(1, max_retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.execute(text_query("SELECT 1"))
            logger.info("Database connection established.")
            return
        except Exception as exc:
            if attempt == max_retries:
                logger.error("Failed to connect to database after %d attempts.", max_retries)
                raise
            logger.warning(
                "Database connection attempt %d/%d failed: %s. Retrying in %.1fs...",
                attempt, max_retries, exc, retry_delay,
            )
            await asyncio.sleep(retry_delay)


def text_query(sql: str):
    """Helper to create a text clause."""
    from sqlalchemy import text
    return text(sql)


async def dispose_engine() -> None:
    """Clean up the engine on shutdown."""
    await engine.dispose()
