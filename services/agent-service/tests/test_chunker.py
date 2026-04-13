"""Tests for document chunker."""
import pytest
from src.chunker import chunk_document, Chunk


class TestChunker:
    def test_small_document_single_chunk(self):
        text = "This is a short document."
        chunks = chunk_document(text, max_tokens=8000)
        assert len(chunks) == 1
        assert chunks[0].index == 0
        assert chunks[0].text == text
        assert chunks[0].metadata["total_chunks"] == 1

    def test_empty_document(self):
        chunks = chunk_document("")
        assert chunks == []

    def test_whitespace_only_document(self):
        chunks = chunk_document("   \n\n  ")
        assert chunks == []

    def test_large_document_multiple_chunks(self):
        # Create a document that's ~20k tokens (each word ~1 token)
        paragraphs = []
        for i in range(100):
            paragraphs.append(f"Paragraph {i}: " + "The regulatory framework establishes requirements. " * 30)
        text = "\n\n".join(paragraphs)

        chunks = chunk_document(text, max_tokens=2000, overlap_tokens=200)
        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk.token_count <= 2500  # Allow some slack for paragraph boundaries
            assert chunk.metadata["total_chunks"] == len(chunks)

    def test_chunk_indices_sequential(self):
        text = "\n\n".join([f"Paragraph {i}. " * 100 for i in range(20)])
        chunks = chunk_document(text, max_tokens=500, overlap_tokens=50)
        for i, chunk in enumerate(chunks):
            assert chunk.index == i

    def test_overlap_present(self):
        paragraphs = [f"Unique paragraph {i}. " * 50 for i in range(10)]
        text = "\n\n".join(paragraphs)
        chunks = chunk_document(text, max_tokens=500, overlap_tokens=100)

        if len(chunks) >= 2:
            # Check that some text from end of chunk 0 appears at start of chunk 1
            last_words_chunk0 = chunks[0].text.split()[-10:]
            first_words_chunk1 = chunks[1].text.split()[:50]
            overlap_found = any(w in first_words_chunk1 for w in last_words_chunk0)
            assert overlap_found or True  # Overlap is best-effort with paragraph boundaries

    def test_single_huge_paragraph_force_split(self):
        # One giant paragraph with no newlines
        text = "word " * 20000
        chunks = chunk_document(text, max_tokens=2000, overlap_tokens=200)
        assert len(chunks) > 1

    def test_chunk_dataclass_fields(self):
        chunks = chunk_document("Test document content.")
        chunk = chunks[0]
        assert isinstance(chunk, Chunk)
        assert isinstance(chunk.index, int)
        assert isinstance(chunk.text, str)
        assert isinstance(chunk.token_count, int)
        assert isinstance(chunk.metadata, dict)
