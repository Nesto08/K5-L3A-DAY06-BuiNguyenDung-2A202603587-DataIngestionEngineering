
"""Read and normalize source data."""

from pathlib import Path
import re
import unicodedata
import fitz
from .models import DocumentPage

def load_pdf(path: Path, document_id: str, source: str) -> list[DocumentPage]:
    """Extract text from each PDF page and keep metadata."""
    pages = []

    with fitz.open(path) as pdf:
        for i, page in enumerate(pdf):
            text = normalize_text(page.get_text("text"))

            if not text:
                print(f"Warning: Page {i + 1} has no text")
                continue

            pages.append(DocumentPage(
                document_id=document_id,
                source=source,
                page=i + 1,
                text=text,
                metadata={"page": i + 1}
            ))

    return pages

def normalize_text(text: str) -> str:
    """Normalize Unicode and whitespace."""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
