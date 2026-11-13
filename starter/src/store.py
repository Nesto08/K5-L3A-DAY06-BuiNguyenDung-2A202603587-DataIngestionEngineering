import math
from typing import Any
import chromadb
from .models import Chunk
class PgVectorStore:
    def __init__(self, database_url: str, dimensions: int) -> None:
        """Initialize persistent vector store."""
        if dimensions <= 0:
            raise ValueError("Invalid dimensions")

        self.dimensions = dimensions
        self.client = chromadb.PersistentClient(path=database_url)

    def create_schema(self) -> None:
        """ChromaDB creates collections automatically."""
        pass

    def upsert(self, strategy: str, chunks: list[Chunk],
               vectors: list[list[float]]) -> None:
        """Save chunks and remove obsolete IDs."""
        if len(chunks) != len(vectors):
            raise ValueError("Chunks and vectors count mismatch")

        if len({c.chunk_id for c in chunks}) != len(chunks):
            raise ValueError("Duplicate chunk IDs")

        if any(len(v) != self.dimensions or
               not all(math.isfinite(x) for x in v) for v in vectors):
            raise ValueError("Invalid vector dimensions or values")

        collection = self.client.get_or_create_collection(
            name=f"lab06_{strategy.lower()}",
            metadata={"hnsw:space": "cosine"}
        )

        ids = [c.chunk_id for c in chunks]

        for i in range(0, len(chunks), 100):
            batch = chunks[i:i + 100]
            collection.upsert(
                ids=[c.chunk_id for c in batch],
                documents=[c.text for c in batch],
                embeddings=vectors[i:i + 100],
                metadatas=[
                    {
                        **c.metadata,
                        "document_id": c.document_id,
                        "source": c.source,
                        "page": c.page
                    }
                    for c in batch
                ]
            )

        old_ids = collection.get(include=[])["ids"]
        obsolete = list(set(old_ids) - set(ids))

        for i in range(0, len(obsolete), 100):
            collection.delete(ids=obsolete[i:i + 100])

    def search(self, strategy: str, query_vector: list[float],
               top_k: int = 3,
               filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Search top-k vectors with optional metadata filters."""
        if len(query_vector) != self.dimensions:
            raise ValueError("Invalid query vector dimensions")
        if not all(math.isfinite(x) for x in query_vector):
            raise ValueError("Invalid query vector values")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        collection = self.client.get_collection(
            name=f"lab06_{strategy.lower()}"
        )

        allowed = {"document_id", "source", "page", "chapter",
                   "section", "category", "year", "language"}

        if filters:
            if any(k not in allowed for k in filters):
                raise ValueError("Unsupported metadata filter")
            if any(type(v) not in (str, int, float, bool)
                   for v in filters.values()):
                raise ValueError("Invalid metadata filter value")

        conditions = [{k: {"$eq": v}} for k, v in (filters or {}).items()]
        where = (conditions[0] if len(conditions) == 1 else
                 {"$and": conditions} if conditions else None)

        if collection.count() == 0:
            return []

        result = collection.query(
            query_embeddings=[query_vector],
            n_results=min(top_k, collection.count()),
            where=where,
            include=["documents", "metadatas", "distances"]
        )

        return [
            {
                "chunk_id": cid,
                "text": text,
                "score": 1 - dist,
                "distance": dist,
                "metadata": meta
            }
            for cid, text, dist, meta in zip(
                result["ids"][0],
                result["documents"][0],
                result["distances"][0],
                result["metadatas"][0]
            )
        ]