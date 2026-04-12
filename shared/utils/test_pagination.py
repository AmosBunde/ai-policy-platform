"""Tests for pagination helpers."""
import pytest
from pydantic import ValidationError

from shared.utils.pagination import PaginatedResponse, PaginationParams


class TestPaginationParams:
    def test_defaults(self):
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 20

    def test_custom_values(self):
        params = PaginationParams(page=3, page_size=50)
        assert params.page == 3
        assert params.page_size == 50

    def test_offset_calculation(self):
        params = PaginationParams(page=1, page_size=20)
        assert params.offset == 0

        params = PaginationParams(page=3, page_size=10)
        assert params.offset == 20

        params = PaginationParams(page=5, page_size=25)
        assert params.offset == 100

    def test_page_minimum(self):
        with pytest.raises(ValidationError):
            PaginationParams(page=0)

    def test_page_maximum(self):
        params = PaginationParams(page=1000)
        assert params.page == 1000

        with pytest.raises(ValidationError):
            PaginationParams(page=1001)

    def test_page_size_minimum(self):
        params = PaginationParams(page_size=1)
        assert params.page_size == 1

        with pytest.raises(ValidationError):
            PaginationParams(page_size=0)

    def test_page_size_maximum(self):
        params = PaginationParams(page_size=100)
        assert params.page_size == 100

        with pytest.raises(ValidationError):
            PaginationParams(page_size=101)

    def test_negative_page(self):
        with pytest.raises(ValidationError):
            PaginationParams(page=-1)

    def test_negative_page_size(self):
        with pytest.raises(ValidationError):
            PaginationParams(page_size=-5)


class TestPaginatedResponse:
    def test_basic_response(self):
        resp = PaginatedResponse[str](
            items=["a", "b", "c"],
            total=10,
            page=1,
            page_size=3,
            total_pages=4,
        )
        assert len(resp.items) == 3
        assert resp.total == 10
        assert resp.total_pages == 4

    def test_empty_response(self):
        resp = PaginatedResponse[str](
            items=[],
            total=0,
            page=1,
            page_size=20,
            total_pages=0,
        )
        assert resp.items == []
        assert resp.total == 0

    def test_last_page_partial(self):
        resp = PaginatedResponse[int](
            items=[1, 2],
            total=12,
            page=2,
            page_size=10,
            total_pages=2,
        )
        assert len(resp.items) == 2
        assert resp.page == 2

    def test_generic_type_with_dict(self):
        resp = PaginatedResponse[dict](
            items=[{"id": 1}, {"id": 2}],
            total=2,
            page=1,
            page_size=20,
            total_pages=1,
        )
        assert resp.items[0]["id"] == 1
