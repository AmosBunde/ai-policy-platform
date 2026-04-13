"""Tests for web crawler: HTML extraction, SSRF blocking, timeout."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestWebCrawlerSSRF:
    @pytest.mark.asyncio
    async def test_rejects_private_ip(self):
        from src.crawlers.web_crawler import crawl_web
        with pytest.raises(ValueError, match="private IP"):
            await crawl_web("http://192.168.1.1/page")

    @pytest.mark.asyncio
    async def test_rejects_localhost(self):
        from src.crawlers.web_crawler import crawl_web
        with pytest.raises(ValueError, match="private IP"):
            await crawl_web("http://127.0.0.1/admin")


class TestWebCrawlerExtraction:
    @pytest.mark.asyncio
    async def test_extracts_html_content(self):
        from src.crawlers.web_crawler import crawl_web

        html = """<html><head><title>Test Page</title></head>
        <body><article><p>Main content here.</p></article></body></html>"""

        mock_response = MagicMock()
        mock_response.text = html
        mock_response.content = html.encode()
        mock_response.status_code = 200
        mock_response.url = "https://example.com/page"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.raise_for_status = MagicMock()

        robots_response = MagicMock()
        robots_response.status_code = 404
        robots_response.text = ""

        with patch("src.crawlers.web_crawler.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=[robots_response, mock_response])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            result = await crawl_web("https://example.com/page")
            assert result["title"] == "Test Page"
            assert "Main content here" in result["content"]

    @pytest.mark.asyncio
    async def test_strips_script_tags(self):
        from src.crawlers.web_crawler import crawl_web

        html = """<html><body>
        <script>alert('xss')</script>
        <p>Safe content</p>
        </body></html>"""

        mock_response = MagicMock()
        mock_response.text = html
        mock_response.content = html.encode()
        mock_response.status_code = 200
        mock_response.url = "https://example.com/page"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.raise_for_status = MagicMock()

        robots_response = MagicMock()
        robots_response.status_code = 404

        with patch("src.crawlers.web_crawler.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=[robots_response, mock_response])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            result = await crawl_web("https://example.com/page")
            assert "alert" not in result["content"]
            assert "Safe content" in result["content"]
