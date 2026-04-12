"""Pagination helpers for FastAPI + SQLAlchemy."""
from typing import Generic, TypeVar

from pydantic import BaseModel, Field
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for pagination."""
    page: int = Field(1, ge=1, le=1000)
    page_size: int = Field(20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


async def paginate_query(
    session: AsyncSession,
    query: Select,
    params: PaginationParams,
) -> tuple[list, int]:
    """Apply LIMIT/OFFSET to a SQLAlchemy query and return (rows, total_count).

    Usage:
        items, total = await paginate_query(session, query, params)
        return PaginatedResponse(
            items=items, total=total,
            page=params.page, page_size=params.page_size,
            total_pages=-(-total // params.page_size),
        )
    """
    # Count total rows
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    # Apply pagination
    paginated = query.offset(params.offset).limit(params.page_size)
    result = await session.execute(paginated)
    rows = list(result.scalars().all())

    return rows, total
