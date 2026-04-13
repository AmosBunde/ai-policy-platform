"""RSS/Atom feed crawler with SSRF prevention."""
import logging
from dataclasses import dataclass, field

import feedparser
import httpx

from src.crawlers.ssrf_guard import validate_url

logger = logging.getLogger(__name__)

_USER_AGENT = "RegulatorAI-Bot/1.0 (+https://regulatorai.com/bot)"
_TIMEOUT = 30.0
_MAX_CONTENT_SIZE = 10 * 1024 * 1024  # 10MB


@dataclass
class FeedEntry:
    title: str
    link: str
    content: str
    published: str | None = None
    external_id: str | None = None
    metadata: dict = field(default_factory=dict)


async def crawl_rss(feed_url: str) -> list[FeedEntry]:
    """Fetch and parse an RSS/Atom feed.

    Raises ValueError for SSRF attempts or invalid URLs.
    """
    validate_url(feed_url)

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.get(
            feed_url,
            headers={"User-Agent": _USER_AGENT},
            follow_redirects=True,
        )
        response.raise_for_status()

        if len(response.content) > _MAX_CONTENT_SIZE:
            raise ValueError(f"Feed content exceeds {_MAX_CONTENT_SIZE} bytes")

    feed = feedparser.parse(response.text)

    if feed.bozo and not feed.entries:
        logger.warning("Malformed feed at %s: %s", feed_url, feed.bozo_exception)
        return []

    entries = []
    for entry in feed.entries:
        content = ""
        if hasattr(entry, "content") and entry.content:
            content = entry.content[0].get("value", "")
        elif hasattr(entry, "summary"):
            content = entry.summary or ""
        elif hasattr(entry, "description"):
            content = entry.description or ""

        entries.append(FeedEntry(
            title=entry.get("title", "Untitled"),
            link=entry.get("link", ""),
            content=content,
            published=entry.get("published"),
            external_id=entry.get("id"),
            metadata={
                "author": entry.get("author"),
                "tags": [t.get("term") for t in entry.get("tags", [])],
            },
        ))

    logger.info("Crawled %d entries from %s", len(entries), feed_url)
    return entries
