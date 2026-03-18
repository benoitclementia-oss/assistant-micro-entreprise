"""Recherche vectorielle dans Qdrant (RAG) pour l'agent Assistant Micro-Entreprise."""

import logging

from qdrant_client import QdrantClient
from scripts import config
from scripts.embedding import generate_embeddings

logger = logging.getLogger(__name__)

_qdrant = QdrantClient(url=config.QDRANT_URL)

ALL_COLLECTIONS = list(config.COLLECTIONS.keys())


def search(
    query: str,
    collections: list[str] | None = None,
    top_k: int = 10,
) -> list[dict]:
    """Recherche sémantique dans les collections Qdrant.

    Retourne les top_k résultats triés par score décroissant.
    """
    if collections is None:
        collections = ALL_COLLECTIONS

    query_vector = generate_embeddings([query])[0]

    all_results: list[dict] = []
    for col in collections:
        if col not in ALL_COLLECTIONS:
            logger.warning("Collection inconnue : %s", col)
            continue
        try:
            response = _qdrant.query_points(
                collection_name=col,
                query=query_vector,
                limit=top_k,
            )
            hits = response.points
        except Exception:
            logger.exception("Erreur recherche Qdrant dans %s", col)
            continue

        for hit in hits:
            payload = hit.payload or {}
            all_results.append(
                {
                    "score": hit.score,
                    "collection": col,
                    "article_id": payload.get("article_id", ""),
                    "titre": payload.get("titre", ""),
                    "texte": payload.get("texte", ""),
                    "code_source": payload.get("code_source", ""),
                    "chunk_index": payload.get("chunk_index", 0),
                }
            )

    all_results.sort(key=lambda r: r["score"], reverse=True)
    return all_results[:top_k]


def format_context(results: list[dict]) -> str:
    """Formate les résultats RAG en contexte lisible pour le prompt LLM."""
    if not results:
        return "Aucun résultat trouvé dans la base juridique."

    parts: list[str] = []
    for i, r in enumerate(results, 1):
        header = f"[{i}] {r['titre']}"
        if r["code_source"]:
            header += f" — {r['code_source']}"
        if r["article_id"]:
            header += f" ({r['article_id']})"
        parts.append(f"{header}\n{r['texte']}")

    return "\n\n---\n\n".join(parts)
