"""Chargement de documents dans Qdrant."""

import hashlib
import logging

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from . import config

logger = logging.getLogger(__name__)

BATCH_SIZE = 100


def _make_point_id(article_id: str, chunk_index: int) -> str:
    """Generer un ID deterministe pour un point Qdrant."""
    raw = f"{article_id}_{chunk_index}"
    return hashlib.md5(raw.encode()).hexdigest()


class QdrantLoader:
    def __init__(self, url: str | None = None) -> None:
        self._client = QdrantClient(url=url or config.QDRANT_URL)

    def ensure_collection(self, name: str) -> None:
        """Creer la collection si elle n'existe pas."""
        collections = [c.name for c in self._client.get_collections().collections]
        if name not in collections:
            logger.info("Creation de la collection '%s'", name)
            self._client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=config.EMBEDDING_DIM,
                    distance=Distance.COSINE,
                ),
            )
        else:
            logger.info("Collection '%s' existante", name)

    def upsert_points(
        self,
        collection: str,
        articles: list[dict],
        chunks_per_article: list[list[str]],
        embeddings_per_article: list[list[list[float]]],
        dry_run: bool = False,
    ) -> int:
        """Inserer les articles chunkes dans Qdrant.

        Retourne le nombre de points inserés.
        """
        points: list[PointStruct] = []

        for article, chunks, embeddings in zip(
            articles, chunks_per_article, embeddings_per_article
        ):
            for chunk_idx, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
                point_id = _make_point_id(article["article_id"], chunk_idx)
                payload = {
                    "titre": article.get("titre", ""),
                    "texte": chunk_text,
                    "source": "legifrance",
                    "code_source": article.get("code_source", ""),
                    "article_id": article.get("article_id", ""),
                    "date_publication": article.get("date_publication", ""),
                    "categorie": article.get("categorie", ""),
                    "etat": article.get("etat", "VIGUEUR"),
                    "chunk_index": chunk_idx,
                }
                points.append(PointStruct(id=point_id, vector=embedding, payload=payload))

        if dry_run:
            logger.info(
                "[DRY RUN] %d points prets pour '%s' (non inseres)",
                len(points),
                collection,
            )
            return len(points)

        # Upsert par batch
        inserted = 0
        for i in range(0, len(points), BATCH_SIZE):
            batch = points[i : i + BATCH_SIZE]
            self._client.upsert(collection_name=collection, points=batch)
            inserted += len(batch)
            logger.info(
                "  Upsert %d/%d points dans '%s'",
                inserted,
                len(points),
                collection,
            )

        return inserted

    def count_points(self, collection: str) -> int:
        """Compter le nombre de points dans une collection."""
        info = self._client.get_collection(collection)
        return info.points_count
