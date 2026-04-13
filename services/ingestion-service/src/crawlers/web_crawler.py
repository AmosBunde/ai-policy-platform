"""Web crawler with robots.txt compliance, rate limiting, and SSRF prevention."""
import asyncio
import logging
import time
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from src.crawlers.ssrf_guard import validate_url

logger = logging.getLogger(__name__)

_USER_AGENT = "RegulatorAI-Bot/1.0 (+https://regulatorai.com/bot)"
_TIMEOUT = 30.0
_MAX_CONTENT_SIZE = 10 * 1024 * 1024  # 10MB
_MIN_REQUEST_INTERVAL = 1.0  # 1 request/second per domain

# Track last request time per domain for rate limiting
_domain_last_request: dict[str, float] = {}


async def _check_robots_txt(base_url: str, client: httpx.AsyncClient) -> bool:
    """Check if crawling is allowed by robots.txt."""
    parsed = urlparse(base_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        resp = await client.get(robots_url, timeout=10.0)
        if resp.status_code == 200:
            text = resp.text.lower()
            # Simple check: if our bot or all bots are disallowed for /
            for line in text.splitlines():
                line = line.strip()
                if line.startswith("user-agent:"):
                    agent = line.split(":", 1)[1].strip()
                    if agent in ("*", "regulatorai-bot"):
                        pass  # Check next lines
                elif line.startswith("disallow:"):
                    path = line.split(":", 1)[1].strip()
                    if path == "/" or urlparse(base_url).path.startswith(path):
                        logger.info("Crawling disallowed by robots.txt: %s", base_url)
                        return False
    except Exception:
        pass  # If we can't fetch robots.txt, assume allowed
    return True


async def _rate_limit(domain: str) -> None:
    """Enforce per-domain rate limiting."""
    now = time.monotonic()
    last = _domain_last_request.get(domain, 0)
    elapsed = now - last
    if elapsed < _MIN_REQUEST_INTERVAL:
        await asyncio.sleep(_MIN_REQUEST_INTERVAL - elapsed)
    _domain_last_request[domain] = time.monotonic()


async def crawl_web(url: str) -> dict:
    """Fetch a web page and extract content.

    Returns dict with title, content, url, metadata.
    Raises ValueError for SSRF attempts.
    """
    validate_url(url)

    parsed = urlparse(url)
    domain = parsed.netloc

    async with httpx.AsyncClient(
        timeout=_TIMEOUT,
        headers={"User-Agent": _USER_AGENT},
        follow_redirects=True,
    ) as client:
        # Check robots.txt
        if not await _check_robots_txt(url, client):
            raise PermissionError(f"Crawling disallowed by robots.txt: {url}")

        # Rate limit per domain
        await _rate_limit(domain)

        response = await client.get(url)
        response.raise_for_status()

        if len(response.content) > _MAX_CONTENT_SIZE:
            raise ValueError(f"Page content exceeds {_MAX_CONTENT_SIZE} bytes")

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove dangerous elements
    for tag in soup(["script", "style", "iframe", "object", "embed", "form", "noscript"]):
        tag.decompose()

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    # Extract main content (prefer article/main tags)
    main_content = soup.find("article") or soup.find("main") or soup.find("body")
    text = main_content.get_text(separator="\n", strip=True) if main_content else ""

    # Extract metadata
    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag and meta_tag.get("content"):
        meta_desc = meta_tag["content"]

    return {
        "title": title,
        "content": text,
        "url": str(response.url),
        "metadata": {
            "description": meta_desc,
            "status_code": response.status_code,
            "content_type": response.headers.get("content-type", ""),
        },
    }
