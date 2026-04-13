"""Elasticsearch client: index mapping, BM25 search, highlighting, facets, autocomplete."""
import html
import logging
import re
from typing import Any

from elasticsearch import AsyncElasticsearch

from shared.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

INDEX_NAME = "regulatory_documents"

INDEX_MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "regulatory_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "stop", "snowball"],
                }
            }
        },
    },
    "mappings": {
        "properties": {
            "document_id": {"type": "keyword"},
            "title": {
                "type": "text",
                "analyzer": "regulatory_analyzer",
                "fields": {"keyword": {"type": "keyword"}},
            },
            "content": {
                "type": "text",
                "analyzer": "regulatory_analyzer",
            },
            "jurisdiction": {"type": "keyword"},
            "category": {"type": "keyword"},
            "document_type": {"type": "keyword"},
            "urgency_level": {"type": "keyword"},
            "status": {"type": "keyword"},
            "published_at": {"type": "date"},
            "created_at": {"type": "date"},
            "url": {"type": "keyword"},
            "summary": {"type": "text", "analyzer": "regulatory_analyzer"},
            "suggest": {
                "type": "completion",
                "analyzer": "simple",
            },
        }
    },
}

# Control characters to strip from queries
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")


def sanitize_query(query: str) -> str:
    """Sanitize search query: strip control chars, limit length."""
    query = _CONTROL_CHAR_RE.sub("", query)
    return query.strip()[:500]


def escape_snippet(text: str) -> str:
    """HTML-escape search result snippets to prevent stored XSS."""
    # Preserve ES highlight tags, escape everything else
    text = text.replace("<em>", "___EM_OPEN___").replace("</em>", "___EM_CLOSE___")
    text = html.escape(text)
    text = text.replace("___EM_OPEN___", "<em>").replace("___EM_CLOSE___", "</em>")
    return text


def is_wildcard_only(query: str) -> bool:
    """Reject wildcard-only queries that could exhaust resources."""
    stripped = query.replace("*", "").replace("?", "").strip()
    return len(stripped) == 0 and len(query) > 0


class ESClient:
    """Async Elasticsearch client wrapper."""

    def __init__(self, es_url: str | None = None):
        url = es_url or settings.elasticsearch_url
        self._es = AsyncElasticsearch(url, verify_certs=False)

    async def ensure_index(self) -> None:
        """Create index if it doesn't exist."""
        if not await self._es.indices.exists(index=INDEX_NAME):
            await self._es.indices.create(index=INDEX_NAME, body=INDEX_MAPPING)
            logger.info("Created index: %s", INDEX_NAME)

    async def index_document(self, doc_id: str, body: dict) -> None:
        """Index a document. Body is parameterized, no string interpolation."""
        # Add completion suggester data
        body["suggest"] = {
            "input": [body.get("title", "")],
            "weight": 10,
        }
        await self._es.index(index=INDEX_NAME, id=doc_id, body=body)

    async def search(
        self,
        query: str,
        jurisdiction: str | None = None,
        category: str | None = None,
        urgency_level: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """BM25 search with highlighting and filters. All params are parameterized."""
        safe_query = sanitize_query(query)
        if not safe_query or is_wildcard_only(safe_query):
            return {"hits": [], "total": 0}

        must = [{"multi_match": {
            "query": safe_query,
            "fields": ["title^3", "summary^2", "content"],
            "type": "best_fields",
        }}]

        filters = []
        if jurisdiction:
            filters.append({"term": {"jurisdiction": jurisdiction}})
        if category:
            filters.append({"term": {"category": category}})
        if urgency_level:
            filters.append({"term": {"urgency_level": urgency_level}})
        if date_from or date_to:
            date_range: dict[str, Any] = {}
            if date_from:
                date_range["gte"] = date_from
            if date_to:
                date_range["lte"] = date_to
            filters.append({"range": {"published_at": date_range}})

        body = {
            "query": {
                "bool": {
                    "must": must,
                    "filter": filters,
                }
            },
            "highlight": {
                "fields": {
                    "content": {"fragment_size": 150, "number_of_fragments": 3},
                    "title": {"fragment_size": 150, "number_of_fragments": 1},
                },
                "pre_tags": ["<em>"],
                "post_tags": ["</em>"],
            },
            "from": (page - 1) * page_size,
            "size": min(page_size, 100),
        }

        result = await self._es.search(index=INDEX_NAME, body=body)

        hits = []
        for hit in result["hits"]["hits"]:
            highlights = []
            for field_highlights in (hit.get("highlight") or {}).values():
                highlights.extend(escape_snippet(h) for h in field_highlights)

            hits.append({
                "document_id": hit["_source"].get("document_id", hit["_id"]),
                "title": hit["_source"].get("title", ""),
                "score": hit["_score"],
                "highlights": highlights,
                "jurisdiction": hit["_source"].get("jurisdiction"),
                "published_at": hit["_source"].get("published_at"),
                "urgency_level": hit["_source"].get("urgency_level"),
            })

        return {
            "hits": hits,
            "total": result["hits"]["total"]["value"],
        }

    async def suggest(self, prefix: str, size: int = 5) -> list[str]:
        """Completion suggester for autocomplete."""
        safe_prefix = sanitize_query(prefix)
        if not safe_prefix:
            return []

        body = {
            "suggest": {
                "title_suggest": {
                    "prefix": safe_prefix,
                    "completion": {
                        "field": "suggest",
                        "size": min(size, 10),
                        "skip_duplicates": True,
                    },
                }
            }
        }

        result = await self._es.search(index=INDEX_NAME, body=body)
        options = result.get("suggest", {}).get("title_suggest", [{}])[0].get("options", [])
        return [opt["text"] for opt in options]

    async def get_facets(self) -> dict:
        """Aggregations for faceted search."""
        body = {
            "size": 0,
            "aggs": {
                "jurisdictions": {"terms": {"field": "jurisdiction", "size": 50}},
                "categories": {"terms": {"field": "category", "size": 50}},
                "urgency_levels": {"terms": {"field": "urgency_level", "size": 10}},
            },
        }

        result = await self._es.search(index=INDEX_NAME, body=body)
        aggs = result.get("aggregations", {})

        return {
            "jurisdictions": [b["key"] for b in aggs.get("jurisdictions", {}).get("buckets", [])],
            "categories": [b["key"] for b in aggs.get("categories", {}).get("buckets", [])],
            "urgency_levels": [b["key"] for b in aggs.get("urgency_levels", {}).get("buckets", [])],
        }

    async def close(self) -> None:
        await self._es.close()
