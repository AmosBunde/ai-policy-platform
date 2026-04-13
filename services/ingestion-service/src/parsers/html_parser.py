"""HTML content extraction with security sanitization."""
import re

from bs4 import BeautifulSoup


_EVENT_HANDLER_RE = re.compile(r"\s+on\w+\s*=", re.IGNORECASE)


def parse_html(html_content: str) -> dict:
    """Extract clean text from HTML, stripping all dangerous elements.

    Returns dict with title, content, metadata.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove dangerous elements
    for tag in soup(["script", "style", "iframe", "object", "embed", "form",
                     "noscript", "link", "meta", "base"]):
        tag.decompose()

    # Remove event handlers from remaining tags
    for tag in soup.find_all(True):
        attrs_to_remove = [attr for attr in tag.attrs if attr.lower().startswith("on")]
        for attr in attrs_to_remove:
            del tag[attr]
        # Remove javascript: URIs
        if tag.get("href", "").strip().lower().startswith("javascript:"):
            tag["href"] = "#"
        if tag.get("src", "").strip().lower().startswith("javascript:"):
            del tag["src"]

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    # Extract clean text
    main = soup.find("article") or soup.find("main") or soup.find("body") or soup
    content = main.get_text(separator="\n", strip=True)

    return {
        "title": title,
        "content": content,
        "metadata": {"format": "html"},
    }
