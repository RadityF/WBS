from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.config import settings


@dataclass
class RetrievalItem:
    score: float
    text: str
    metadata: dict[str, Any]


class QdrantService:
    def __init__(self) -> None:
        api_key = settings.qdrant_api_key or None
        self.client = QdrantClient(url=settings.qdrant_url, api_key=api_key)
        self.collection = settings.qdrant_collection

    def ensure_collection(self, vector_size: int, collection_name: str | None = None) -> None:
        collection = collection_name or self.collection
        try:
            info = self.client.get_collection(collection)
            existing_size = int(info.config.params.vectors.size)
            if existing_size == vector_size:
                return
            self.client.delete_collection(collection)
        except Exception:
            pass

        self.client.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

    def recreate_collection(self, vector_size: int, collection_name: str | None = None) -> None:
        collection = collection_name or self.collection
        self.client.recreate_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

    def upsert(self, points: list[PointStruct], collection_name: str | None = None) -> None:
        collection = collection_name or self.collection
        self.client.upsert(collection_name=collection, points=points)

    def search(self, vector: list[float], top_k: int, collection_name: str | None = None) -> list[RetrievalItem]:
        collection = collection_name or self.collection
        try:
            hits = self.client.search(
                collection_name=collection,
                query_vector=vector,
                limit=top_k,
                with_payload=True,
            )
        except Exception:
            return []

        items: list[RetrievalItem] = []
        for hit in hits:
            payload = hit.payload or {}
            items.append(
                RetrievalItem(
                    score=float(hit.score or 0.0),
                    text=str(payload.get("text", "")),
                    metadata={k: v for k, v in payload.items() if k != "text"},
                )
            )
        return items
