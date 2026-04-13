"""Hybrid search: Reciprocal Rank Fusion combining keyword (ES) and semantic (pgvector)."""
import logging

logger = logging.getLogger(__name__)


def reciprocal_rank_fusion(
    keyword_results: list[dict],
    semantic_results: list[dict],
    k: int = 60,
    alpha: float = 0.5,
) -> list[dict]:
    """Combine keyword and semantic results using Reciprocal Rank Fusion.

    Args:
        keyword_results: List of dicts with 'document_id' and 'score'.
        semantic_results: List of dicts with 'document_id' and 'similarity'.
        k: RRF constant (default 60).
        alpha: Weight for keyword results (1-alpha for semantic). Default 0.5.

    Returns:
        Merged, deduplicated results sorted by RRF score.
    """
    scores: dict[str, float] = {}
    meta: dict[str, dict] = {}

    # Keyword results
    for rank, result in enumerate(keyword_results):
        doc_id = result["document_id"]
        rrf_score = alpha * (1.0 / (k + rank + 1))
        scores[doc_id] = scores.get(doc_id, 0.0) + rrf_score
        if doc_id not in meta:
            meta[doc_id] = result

    # Semantic results
    for rank, result in enumerate(semantic_results):
        doc_id = result["document_id"]
        rrf_score = (1.0 - alpha) * (1.0 / (k + rank + 1))
        scores[doc_id] = scores.get(doc_id, 0.0) + rrf_score
        if doc_id not in meta:
            meta[doc_id] = {
                "document_id": doc_id,
                "title": "",
                "score": 0,
                "highlights": [],
                "snippet": result.get("chunk_text", "")[:200],
            }

    # Build merged results sorted by RRF score
    merged = []
    for doc_id in sorted(scores, key=scores.get, reverse=True):
        entry = dict(meta[doc_id])
        entry["score"] = scores[doc_id]
        entry["source"] = _determine_source(doc_id, keyword_results, semantic_results)
        merged.append(entry)

    return merged


def _determine_source(doc_id: str, keyword_results: list, semantic_results: list) -> str:
    """Determine which source(s) contributed this result."""
    in_keyword = any(r["document_id"] == doc_id for r in keyword_results)
    in_semantic = any(r["document_id"] == doc_id for r in semantic_results)
    if in_keyword and in_semantic:
        return "hybrid"
    elif in_keyword:
        return "keyword"
    return "semantic"
