
"""Choose a real embedding provider (API or local)."""

from typing import Protocol
from openai import OpenAI

class Embedder(Protocol):
    model_name: str
    dimensions: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in the same order."""
        ...

    def embed_query(self, question: str) -> list[float]:
        """Return a query vector compatible with stored vectors."""
        ...
class MyEmbedder:
    """OpenAI embedding provider."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.client = OpenAI()

        dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536
        }

        if model_name not in dimensions:
            raise ValueError(f"Unsupported model: {model_name}")

        self.dimensions = dimensions[model_name]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Convert document texts into embeddings."""
        if not texts:
            return []

        if any(not text.strip() for text in texts):
            raise ValueError("Empty document text")

        vectors = []

        for i in range(0, len(texts), 100):
            batch = texts[i:i + 100]

            response = self.client.embeddings.create(
                model=self.model_name,
                input=batch
            )

            ordered = sorted(response.data, key=lambda x: x.index)
            vectors.extend(item.embedding for item in ordered)

        return vectors

    def embed_query(self, question: str) -> list[float]:
        """Convert a query into an embedding."""
        if not question.strip():
            raise ValueError("Empty query")

        response = self.client.embeddings.create(
            model=self.model_name,
            input=question
        )

        return response.data[0].embedding

