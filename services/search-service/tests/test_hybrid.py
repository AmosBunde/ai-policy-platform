"""Tests for hybrid search: RRF calculation, deduplication, alpha weighting."""
import pytest
from src.hybrid_search import reciprocal_rank_fusion, _determine_source


class TestRRF:
    def test_basic_fusion(self):
        keyword = [
            {"document_id": "doc1", "title": "Doc 1", "score": 5.0, "highlights": []},
            {"document_id": "doc2", "title": "Doc 2", "score": 3.0, "highlights": []},
        ]
        semantic = [
            {"document_id": "doc2", "chunk_text": "text", "similarity": 0.95},
            {"document_id": "doc3", "chunk_text": "text", "similarity": 0.80},
        ]

        results = reciprocal_rank_fusion(keyword, semantic)
        assert len(results) == 3  # doc1, doc2, doc3 (deduplicated)
        doc_ids = [r["document_id"] for r in results]
        assert "doc1" in doc_ids
        assert "doc2" in doc_ids
        assert "doc3" in doc_ids

    def test_deduplication(self):
        keyword = [
            {"document_id": "doc1", "title": "Title", "score": 5.0, "highlights": []},
        ]
        semantic = [
            {"document_id": "doc1", "chunk_text": "text", "similarity": 0.9},
        ]

        results = reciprocal_rank_fusion(keyword, semantic)
        assert len(results) == 1
        assert results[0]["document_id"] == "doc1"
        # Hybrid doc should score higher than single-source
        assert results[0]["score"] > 0

    def test_doc_in_both_sources_ranks_higher(self):
        keyword = [
            {"document_id": "doc1", "title": "T1", "score": 5.0, "highlights": []},
            {"document_id": "doc2", "title": "T2", "score": 3.0, "highlights": []},
        ]
        semantic = [
            {"document_id": "doc1", "chunk_text": "t", "similarity": 0.95},
            {"document_id": "doc3", "chunk_text": "t", "similarity": 0.80},
        ]

        results = reciprocal_rank_fusion(keyword, semantic)
        # doc1 appears in both, so should rank first
        assert results[0]["document_id"] == "doc1"

    def test_alpha_weighting_keyword_heavy(self):
        keyword = [{"document_id": "kw1", "title": "KW", "score": 5.0, "highlights": []}]
        semantic = [{"document_id": "sem1", "chunk_text": "t", "similarity": 0.9}]

        results = reciprocal_rank_fusion(keyword, semantic, alpha=0.9)
        kw_score = next(r["score"] for r in results if r["document_id"] == "kw1")
        sem_score = next(r["score"] for r in results if r["document_id"] == "sem1")
        assert kw_score > sem_score

    def test_alpha_weighting_semantic_heavy(self):
        keyword = [{"document_id": "kw1", "title": "KW", "score": 5.0, "highlights": []}]
        semantic = [{"document_id": "sem1", "chunk_text": "t", "similarity": 0.9}]

        results = reciprocal_rank_fusion(keyword, semantic, alpha=0.1)
        kw_score = next(r["score"] for r in results if r["document_id"] == "kw1")
        sem_score = next(r["score"] for r in results if r["document_id"] == "sem1")
        assert sem_score > kw_score

    def test_empty_keyword_results(self):
        semantic = [{"document_id": "doc1", "chunk_text": "t", "similarity": 0.9}]
        results = reciprocal_rank_fusion([], semantic)
        assert len(results) == 1

    def test_empty_semantic_results(self):
        keyword = [{"document_id": "doc1", "title": "T", "score": 5.0, "highlights": []}]
        results = reciprocal_rank_fusion(keyword, [])
        assert len(results) == 1

    def test_both_empty(self):
        results = reciprocal_rank_fusion([], [])
        assert results == []

    def test_custom_k_parameter(self):
        keyword = [{"document_id": "doc1", "title": "T", "score": 5.0, "highlights": []}]
        semantic = [{"document_id": "doc2", "chunk_text": "t", "similarity": 0.9}]

        results_k10 = reciprocal_rank_fusion(keyword, semantic, k=10)
        results_k100 = reciprocal_rank_fusion(keyword, semantic, k=100)
        # Lower k gives more weight to top positions
        assert results_k10[0]["score"] > results_k100[0]["score"]


class TestSourceDetermination:
    def test_hybrid_source(self):
        kw = [{"document_id": "doc1"}]
        sem = [{"document_id": "doc1"}]
        assert _determine_source("doc1", kw, sem) == "hybrid"

    def test_keyword_only(self):
        kw = [{"document_id": "doc1"}]
        sem = [{"document_id": "doc2"}]
        assert _determine_source("doc1", kw, sem) == "keyword"

    def test_semantic_only(self):
        kw = [{"document_id": "doc2"}]
        sem = [{"document_id": "doc1"}]
        assert _determine_source("doc1", kw, sem) == "semantic"
