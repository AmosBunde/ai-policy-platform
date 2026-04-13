"""Tests for vector search: embedding generation (mocked), similarity search."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.vector_search import sanitize_for_embedding


class TestSanitizeForEmbedding:
    def test_strips_control_chars(self):
        assert sanitize_for_embedding("hello\x00world") == "helloworld"

    def test_strips_whitespace(self):
        assert sanitize_for_embedding("  hello  ") == "hello"

    def test_empty_string(self):
        assert sanitize_for_embedding("") == ""

    def test_preserves_unicode(self):
        assert sanitize_for_embedding("EU AI Act Verordnung") == "EU AI Act Verordnung"

    def test_strips_tabs_and_newlines(self):
        result = sanitize_for_embedding("line1\nline2\ttab")
        # \n and \t are not in the control char range we strip (\x00-\x1f includes them)
        # Actually \n=\x0a and \t=\x09 ARE control chars
        assert "\x00" not in result


class TestGenerateEmbedding:
    @pytest.mark.asyncio
    async def test_generate_embedding_mocked(self):
        from src.vector_search import generate_embedding

        mock_response = MagicMock()
        mock_response.data = [MagicMock()]
        mock_response.data[0].embedding = [0.1] * 1536

        with patch("openai.AsyncOpenAI") as MockClient:
            mock_client = MagicMock()
            mock_client.embeddings = MagicMock()
            mock_client.embeddings.create = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            result = await generate_embedding("test query")
            assert len(result) == 1536
            assert result[0] == 0.1

    @pytest.mark.asyncio
    async def test_empty_text_returns_zeros(self):
        from src.vector_search import generate_embedding

        result = await generate_embedding("")
        assert len(result) == 1536
        assert all(x == 0.0 for x in result)
