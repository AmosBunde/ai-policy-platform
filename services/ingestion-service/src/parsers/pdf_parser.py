"""PDF text extraction using PyMuPDF with security limits."""
import logging

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def parse_pdf(file_bytes: bytes) -> dict:
    """Extract text and metadata from a PDF.

    Returns dict with title, content, metadata.
    Raises ValueError for oversized or malformed files.
    """
    if len(file_bytes) > _MAX_FILE_SIZE:
        raise ValueError(f"PDF exceeds maximum file size of {_MAX_FILE_SIZE} bytes")

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        raise ValueError(f"Malformed PDF: {exc}") from exc

    try:
        pages_text = []
        for page in doc:
            pages_text.append(page.get_text())

        content = "\n".join(pages_text).strip()

        metadata = doc.metadata or {}
        title = metadata.get("title", "") or ""
        author = metadata.get("author", "") or ""
        creation_date = metadata.get("creationDate", "") or ""

        return {
            "title": title,
            "content": content,
            "metadata": {
                "author": author,
                "creation_date": creation_date,
                "page_count": doc.page_count,
                "format": "pdf",
            },
        }
    finally:
        doc.close()
