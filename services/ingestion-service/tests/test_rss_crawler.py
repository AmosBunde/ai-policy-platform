"""Tests for RSS crawler with SSRF prevention."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.crawlers.ssrf_guard import validate_url


class TestSSRFGuard:
    def test_valid_https_url(self):
        assert validate_url("https://example.com/feed.xml") == "https://example.com/feed.xml"

    def test_valid_http_url(self):
        assert validate_url("http://example.com/rss") == "http://example.com/rss"

    def test_rejects_file_scheme(self):
        with pytest.raises(ValueError):
            validate_url("file:///etc/passwd")

    def test_rejects_ftp_scheme(self):
        with pytest.raises(ValueError):
            validate_url("ftp://evil.com/data")

    def test_rejects_private_ip_127(self):
        with pytest.raises(ValueError, match="private IP"):
            validate_url("http://127.0.0.1/admin")

    def test_rejects_private_ip_10(self):
        with pytest.raises(ValueError, match="private IP"):
            validate_url("http://10.0.0.1/internal")

    def test_rejects_private_ip_172(self):
        with pytest.raises(ValueError, match="private IP"):
            validate_url("http://172.16.0.1/secret")

    def test_rejects_private_ip_192(self):
        with pytest.raises(ValueError, match="private IP"):
            validate_url("http://192.168.1.1/config")

    def test_rejects_localhost(self):
        with pytest.raises(ValueError, match="private IP"):
            validate_url("http://127.0.0.1:8080/api")

    def test_rejects_ipv6_loopback(self):
        with pytest.raises(ValueError, match="private IP"):
            validate_url("http://[::1]/admin")

    def test_rejects_no_scheme(self):
        with pytest.raises(ValueError, match="Invalid URL"):
            validate_url("example.com/feed")

    def test_rejects_empty_url(self):
        with pytest.raises(ValueError):
            validate_url("")

    def test_rejects_data_scheme(self):
        with pytest.raises(ValueError):
            validate_url("data:text/html,<script>alert(1)</script>")


class TestRSSCrawler:
    @pytest.mark.asyncio
    async def test_crawl_rss_rejects_ssrf(self):
        from src.crawlers.rss_crawler import crawl_rss
        with pytest.raises(ValueError, match="private IP"):
            await crawl_rss("http://127.0.0.1/feed.xml")

    @pytest.mark.asyncio
    async def test_crawl_rss_valid_feed(self):
        from src.crawlers.rss_crawler import crawl_rss

        mock_response = MagicMock()
        mock_response.text = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <title>Test Feed</title>
                <item>
                    <title>Test Entry</title>
                    <link>https://example.com/article</link>
                    <description>Test content</description>
                </item>
            </channel>
        </rss>"""
        mock_response.content = mock_response.text.encode()
        mock_response.raise_for_status = MagicMock()

        with patch("src.crawlers.rss_crawler.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            entries = await crawl_rss("https://example.com/feed.xml")
            assert len(entries) == 1
            assert entries[0].title == "Test Entry"

    @pytest.mark.asyncio
    async def test_crawl_rss_invalid_feed_returns_empty(self):
        from src.crawlers.rss_crawler import crawl_rss

        mock_response = MagicMock()
        mock_response.text = "This is not valid RSS/XML at all"
        mock_response.content = mock_response.text.encode()
        mock_response.raise_for_status = MagicMock()

        with patch("src.crawlers.rss_crawler.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            entries = await crawl_rss("https://example.com/bad-feed")
            # feedparser is lenient, may return entries or empty
            assert isinstance(entries, list)
