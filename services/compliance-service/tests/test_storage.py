"""Tests for file storage: local save/retrieve, path traversal prevention."""
import os
import tempfile

import pytest

from src.storage import (
    LocalFileStorage,
    generate_safe_filename,
    validate_filename,
)


class TestFilenameGeneration:
    def test_generates_uuid_filename(self):
        name = generate_safe_filename("pdf")
        assert name.endswith(".pdf")
        assert len(name) == 40  # UUID (36) + ".pdf" (4)

    def test_generates_docx_filename(self):
        name = generate_safe_filename("docx")
        assert name.endswith(".docx")

    def test_generates_html_filename(self):
        name = generate_safe_filename("html")
        assert name.endswith(".html")

    def test_rejects_invalid_extension(self):
        with pytest.raises(ValueError, match="Invalid extension"):
            generate_safe_filename("exe")

    def test_rejects_empty_extension(self):
        with pytest.raises(ValueError):
            generate_safe_filename("")

    def test_strips_dot_prefix(self):
        name = generate_safe_filename(".pdf")
        assert name.endswith(".pdf")


class TestFilenameValidation:
    def test_valid_uuid_pdf(self):
        assert validate_filename("550e8400-e29b-41d4-a716-446655440000.pdf") is True

    def test_valid_uuid_docx(self):
        assert validate_filename("550e8400-e29b-41d4-a716-446655440000.docx") is True

    def test_rejects_path_traversal_dots(self):
        assert validate_filename("../../etc/passwd") is False

    def test_rejects_path_traversal_slash(self):
        assert validate_filename("path/to/file.pdf") is False

    def test_rejects_backslash(self):
        assert validate_filename("path\\file.pdf") is False

    def test_rejects_non_uuid_filename(self):
        assert validate_filename("my-report.pdf") is False

    def test_rejects_empty(self):
        assert validate_filename("") is False

    def test_rejects_just_extension(self):
        assert validate_filename(".pdf") is False


class TestLocalFileStorage:
    @pytest.fixture
    def storage(self, tmp_path):
        return LocalFileStorage(base_dir=str(tmp_path))

    @pytest.mark.asyncio
    async def test_save_and_retrieve(self, storage):
        filename = generate_safe_filename("pdf")
        content = b"fake pdf content"
        path = await storage.save(filename, content)
        assert os.path.exists(path)

        retrieved = await storage.retrieve(filename)
        assert retrieved == content

    @pytest.mark.asyncio
    async def test_exists(self, storage):
        filename = generate_safe_filename("pdf")
        assert await storage.exists(filename) is False

        await storage.save(filename, b"content")
        assert await storage.exists(filename) is True

    @pytest.mark.asyncio
    async def test_rejects_traversal_on_save(self, storage):
        with pytest.raises(ValueError, match="Invalid filename"):
            await storage.save("../../evil.pdf", b"content")

    @pytest.mark.asyncio
    async def test_rejects_traversal_on_retrieve(self, storage):
        with pytest.raises(ValueError, match="Invalid filename"):
            await storage.retrieve("../../../etc/passwd")

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_returns_none(self, storage):
        filename = generate_safe_filename("pdf")
        result = await storage.retrieve(filename)
        assert result is None
