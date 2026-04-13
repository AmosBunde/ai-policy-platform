"""Normalize parsed content to RegulatoryDocument schema."""
import hashlib
import re
from datetime import datetime, timezone

_MAX_CONTENT_LENGTH = 1_000_000  # 1M chars

# Simple language detection heuristics
_LANG_PATTERNS = {
    "en": re.compile(r"\b(the|and|of|to|in|is|that|for|it|with)\b", re.IGNORECASE),
    "fr": re.compile(r"\b(le|la|les|de|du|des|et|en|est|que)\b", re.IGNORECASE),
    "de": re.compile(r"\b(der|die|das|und|in|den|von|zu|ist|mit)\b", re.IGNORECASE),
    "es": re.compile(r"\b(el|la|los|las|de|del|en|que|por|con)\b", re.IGNORECASE),
}

# Dangerous HTML patterns to strip
_DANGEROUS_BLOCK_RE = re.compile(
    r"<\s*(script|iframe|object|embed|form|style)\b[^>]*>.*?</\s*\1\s*>",
    re.IGNORECASE | re.DOTALL,
)
_DANGEROUS_TAG_RE = re.compile(
    r"<\s*/?\s*(script|iframe|object|embed|form|style|link|meta|base)\b[^>]*>",
    re.IGNORECASE,
)


def _sanitize_text(text: str) -> str:
    """Strip dangerous HTML/JS from text."""
    text = _DANGEROUS_BLOCK_RE.sub("", text)
    text = _DANGEROUS_TAG_RE.sub("", text)
    return text.strip()


def generate_content_hash(content: str) -> str:
    """SHA-256 hex digest of content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def detect_language(text: str) -> str:
    """Detect language using simple word-frequency heuristics."""
    sample = text[:5000]
    scores = {}
    for lang, pattern in _LANG_PATTERNS.items():
        scores[lang] = len(pattern.findall(sample))
    if not scores or max(scores.values()) == 0:
        return "en"
    return max(scores, key=scores.get)


def normalize(
    title: str,
    content: str,
    url: str | None = None,
    jurisdiction: str | None = None,
    document_type: str | None = None,
    source_id: str | None = None,
    external_id: str | None = None,
    published_at: str | None = None,
    raw_metadata: dict | None = None,
) -> dict:
    """Normalize parsed content into RegulatoryDocument-compatible dict.

    Sanitizes all text, enforces max content length, generates content hash,
    and detects language.
    """
    title = _sanitize_text(title)[:500]
    content = _sanitize_text(content)

    if len(content) > _MAX_CONTENT_LENGTH:
        content = content[:_MAX_CONTENT_LENGTH]

    content_hash = generate_content_hash(content)
    language = detect_language(content)

    pub_at = None
    if published_at:
        try:
            pub_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pub_at = None

    return {
        "title": title or "Untitled",
        "content": content,
        "content_hash": content_hash,
        "url": url,
        "jurisdiction": (jurisdiction or "")[:100] or None,
        "document_type": (document_type or "")[:50] or None,
        "language": language,
        "source_id": source_id,
        "external_id": external_id,
        "published_at": pub_at,
        "raw_metadata": raw_metadata or {},
        "status": "ingested",
    }
