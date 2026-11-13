import re
from .models import Chunk, DocumentPage

def fixed_size(page: DocumentPage, size: int, overlap: int) -> list[Chunk]:
    """Split text into overlapping chunks."""
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("Invalid size or overlap")

    chunks = []
    text = page.text
    step = size - overlap

    for i, start in enumerate(range(0, len(text), step)):
        part = text[start:start + size]
        if not part.strip():
            continue

        chunks.append(Chunk(
            chunk_id=f"{page.document_id}_{page.page}_fixed_{i}",
            document_id=page.document_id,
            source=page.source,
            page=page.page,
            text=part,
            metadata={**page.metadata, "chunk_type": "fixed"}
        ))

        if start + size >= len(text):
            break

    return chunks

def by_paragraph(page: DocumentPage, max_size: int) -> list[Chunk]:
    """Group paragraphs without exceeding max_size."""
    if max_size <= 0:
        raise ValueError("max_size must be positive")

    paragraphs = re.split(r"\n\s*\n", page.text.strip())
    chunks = []
    current = ""

    def add_chunk(text):
        if text.strip():
            chunks.append(Chunk(
                chunk_id=f"{page.document_id}_{page.page}_para_{len(chunks)}",
                document_id=page.document_id,
                source=page.source,
                page=page.page,
                text=text.strip(),
                metadata={**page.metadata, "chunk_type": "paragraph"}
            ))

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        if current and len(current) + len(paragraph) + 2 > max_size:
            add_chunk(current)
            current = ""

        if len(paragraph) > max_size:
            for start in range(0, len(paragraph), max_size):
                add_chunk(paragraph[start:start + max_size])
        else:
            current = f"{current}\n\n{paragraph}" if current else paragraph

    add_chunk(current)
    return chunks

