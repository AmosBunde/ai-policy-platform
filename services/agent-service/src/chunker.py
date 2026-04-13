"""Document chunker: split by token count with paragraph-aware boundaries."""
import tiktoken
from dataclasses import dataclass


@dataclass
class Chunk:
    index: int
    text: str
    token_count: int
    metadata: dict


def chunk_document(
    text: str,
    max_tokens: int = 8000,
    overlap_tokens: int = 500,
    model: str = "gpt-4o",
) -> list[Chunk]:
    """Split text into chunks by token count, preserving paragraph boundaries.

    Args:
        text: Document text to chunk.
        max_tokens: Maximum tokens per chunk (default 8000).
        overlap_tokens: Overlapping tokens between chunks (default 500).
        model: Model name for tokenizer selection.

    Returns:
        List of Chunk objects with index, text, token_count, and metadata.
    """
    if not text or not text.strip():
        return []

    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    tokens = encoding.encode(text)
    total_tokens = len(tokens)

    if total_tokens <= max_tokens:
        return [Chunk(index=0, text=text, token_count=total_tokens, metadata={"total_chunks": 1})]

    # Split into paragraphs first
    paragraphs = text.split("\n\n")
    if len(paragraphs) <= 1:
        paragraphs = text.split("\n")

    chunks = []
    current_paragraphs: list[str] = []
    current_token_count = 0

    for para in paragraphs:
        para_tokens = len(encoding.encode(para))

        if current_token_count + para_tokens > max_tokens and current_paragraphs:
            # Emit current chunk
            chunk_text = "\n\n".join(current_paragraphs)
            chunks.append(Chunk(
                index=len(chunks),
                text=chunk_text,
                token_count=current_token_count,
                metadata={},
            ))

            # Overlap: keep last paragraphs that fit within overlap_tokens
            overlap_paras: list[str] = []
            overlap_count = 0
            for p in reversed(current_paragraphs):
                p_count = len(encoding.encode(p))
                if overlap_count + p_count <= overlap_tokens:
                    overlap_paras.insert(0, p)
                    overlap_count += p_count
                else:
                    break

            current_paragraphs = overlap_paras
            current_token_count = overlap_count

        # Handle individual paragraphs larger than max_tokens
        if para_tokens > max_tokens:
            if current_paragraphs:
                chunk_text = "\n\n".join(current_paragraphs)
                chunks.append(Chunk(
                    index=len(chunks),
                    text=chunk_text,
                    token_count=current_token_count,
                    metadata={},
                ))
                current_paragraphs = []
                current_token_count = 0

            # Force-split large paragraph by tokens
            para_encoded = encoding.encode(para)
            offset = 0
            while offset < len(para_encoded):
                end = min(offset + max_tokens, len(para_encoded))
                sub_text = encoding.decode(para_encoded[offset:end])
                sub_count = end - offset
                chunks.append(Chunk(
                    index=len(chunks),
                    text=sub_text,
                    token_count=sub_count,
                    metadata={"force_split": True},
                ))
                offset = end - overlap_tokens if end < len(para_encoded) else end
            continue

        current_paragraphs.append(para)
        current_token_count += para_tokens

    if current_paragraphs:
        chunk_text = "\n\n".join(current_paragraphs)
        chunks.append(Chunk(
            index=len(chunks),
            text=chunk_text,
            token_count=current_token_count,
            metadata={},
        ))

    total_chunks = len(chunks)
    for c in chunks:
        c.metadata["total_chunks"] = total_chunks

    return chunks
