"""Script principal d'ingestion Legifrance -> Qdrant.

Usage :
    python -m scripts.ingest                          # toutes les collections
    python -m scripts.ingest --collection lois_fiscales
    python -m scripts.ingest --dry-run                # test sans insertion
    python -m scripts.ingest --fetch-only             # fetch + cache, pas d'embeddings
    python -m scripts.ingest --from-cache             # skip fetch, utilise le cache
    python -m scripts.ingest --resume                 # reprend depuis le cache partiel
"""

import argparse
import json
import logging
import re
import sys
import time
from pathlib import Path

from . import config
from .embedding import chunk_text, generate_embeddings
from .eurlex_client import EurlexClient
from .legifrance_client import LegifranceClient
from .pdf_client import PdfClient
from .qdrant_loader import QdrantLoader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CACHE_DIR = _PROJECT_ROOT / "data" / "cache"


def _strip_html(text: str) -> str:
    """Retirer les balises HTML basiques d'un texte."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _cache_path(collection_name: str) -> Path:
    return _CACHE_DIR / f"{collection_name}.json"


def _save_cache(collection_name: str, articles: list[dict]) -> None:
    """Sauvegarder les articles fetchés en cache local."""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _cache_path(collection_name)
    path.write_text(json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(
        "Cache sauvegardé : %s (%d articles, %.1f Mo)",
        path.name,
        len(articles),
        path.stat().st_size / 1024 / 1024,
    )


def _load_cache(collection_name: str) -> list[dict] | None:
    """Charger les articles depuis le cache local."""
    path = _cache_path(collection_name)
    if not path.exists():
        return None
    articles = json.loads(path.read_text(encoding="utf-8"))
    logger.info("Cache chargé : %s (%d articles)", path.name, len(articles))
    return articles


def _fetch_articles(
    collection_name: str,
    lf_client: LegifranceClient | None,
    resume: bool = False,
    el_client: EurlexClient | None = None,
    pdf_client: PdfClient | None = None,
) -> list[dict]:
    """Fetch les articles depuis Legifrance et/ou EUR-Lex et retourne la liste.

    Le cache est sauvegardé progressivement après chaque source
    (code, requête LODA, ou texte EUR-Lex) pour ne pas perdre les données
    en cas d'interruption (quota, crash, etc.).

    Args:
        resume: Si True, charge le cache existant et saute les sources
                dont les articles sont déjà présents.
        el_client: Client EUR-Lex (requis si la collection a des eurlex_sources).
    """
    coll_config = config.COLLECTIONS[collection_name]
    all_articles: list[dict] = []

    # En mode resume, charger les articles déjà en cache
    cached_code_ids: set[str] = set()
    cached_celex: set[str] = set()
    cached_source_tags: set[str] = set()
    if resume:
        existing = _load_cache(collection_name)
        if existing:
            all_articles = existing
            for art in existing:
                src = art.get("code_source", "")
                if not src.startswith("Recherche:"):
                    cached_code_ids.add(src)
                if art.get("source") == "eurlex":
                    cached_celex.add(art.get("celex", ""))
                if art.get("source") == "pdf":
                    cached_source_tags.add(art.get("source_tag", ""))
            logger.info(
                "Resume : %d articles en cache, codes=%s, celex=%s, pdf_tags=%s",
                len(existing),
                cached_code_ids or "(aucun)",
                cached_celex or "(aucun)",
                cached_source_tags or "(aucun)",
            )

    # 1. Articles depuis les codes Legifrance
    for code in coll_config["codes"]:
        if resume and code["nom"] in cached_code_ids:
            logger.info("Skip code '%s' (déjà en cache)", code["nom"])
            continue
        if lf_client is None:
            logger.warning("LegifranceClient absent, skip code '%s'", code["nom"])
            continue
        articles = lf_client.fetch_articles_from_code(code["id"], code["nom"])
        for art in articles:
            art["categorie"] = collection_name
        all_articles.extend(articles)
        _save_cache(collection_name, all_articles)
        logger.info("  Cache progressif sauvegardé après '%s'", code["nom"])

    # 2. Articles depuis les recherches LODA
    for query in coll_config["recherches_loda"]:
        if lf_client is None:
            logger.warning("LegifranceClient absent, skip recherche '%s'", query)
            continue
        skip_tids: set[str] | None = None
        articles = lf_client.fetch_articles_from_search(
            query,
            fonds="LODA_ETAT",
            skip_text_ids=skip_tids,
        )
        for art in articles:
            art["categorie"] = collection_name
        all_articles.extend(articles)
        _save_cache(collection_name, all_articles)
        logger.info("  Cache progressif sauvegardé après recherche '%s'", query)

    # 3. Articles depuis EUR-Lex
    for source in coll_config.get("eurlex_sources", []):
        celex = source["celex"]
        if resume and celex in cached_celex:
            logger.info("Skip EUR-Lex '%s' (déjà en cache)", celex)
            continue
        if el_client is None:
            logger.warning("EurlexClient absent, skip '%s'", source["nom"])
            continue
        articles = el_client.fetch_regulation(celex, source["nom"])
        for art in articles:
            art["categorie"] = collection_name
        all_articles.extend(articles)
        _save_cache(collection_name, all_articles)
        logger.info("  Cache progressif sauvegardé après EUR-Lex '%s'", celex)

    # 4. Articles depuis PDFs publics (ANSSI, ENISA, CNIL, etc.)
    for source in coll_config.get("pdf_sources", []):
        tag = source["source_tag"]
        if resume and tag in cached_source_tags:
            logger.info("Skip PDF '%s' (déjà en cache)", tag)
            continue
        if pdf_client is None:
            logger.warning("PdfClient absent, skip '%s'", source["nom"])
            continue
        articles = pdf_client.fetch_document(source["url"], source["nom"], tag)
        for art in articles:
            art["categorie"] = collection_name
        all_articles.extend(articles)
        _save_cache(collection_name, all_articles)
        logger.info("  Cache progressif sauvegardé après PDF '%s'", tag)

    # Filtrer : uniquement les articles en vigueur
    all_articles = [a for a in all_articles if a.get("etat") == "VIGUEUR"]

    # Deduplication par article_id
    seen: set[str] = set()
    unique_articles: list[dict] = []
    for art in all_articles:
        if art["article_id"] not in seen:
            seen.add(art["article_id"])
            unique_articles.append(art)

    logger.info(
        "Collection '%s' : %d articles en vigueur (uniques)",
        collection_name,
        len(unique_articles),
    )
    return unique_articles


def _embed_and_upsert(
    collection_name: str,
    articles: list[dict],
    loader: QdrantLoader,
    dry_run: bool = False,
) -> dict:
    """Chunk, embed et upsert les articles dans Qdrant."""
    stats = {"articles": len(articles), "chunks": 0, "points": 0}

    if not articles:
        logger.warning("Aucun article pour '%s', passage a la suite.", collection_name)
        return stats

    # Chunking
    all_chunks: list[list[str]] = []
    for art in articles:
        texte = _strip_html(art.get("texte", ""))
        if not texte:
            texte = art.get("titre", "")
        chunks = chunk_text(texte)
        all_chunks.append(chunks)
        stats["chunks"] += len(chunks)

    logger.info(
        "  %d chunks générés à partir de %d articles",
        stats["chunks"],
        stats["articles"],
    )

    # Embeddings
    flat_chunks = [c for chunks in all_chunks for c in chunks]
    logger.info("  Génération des embeddings pour %d chunks...", len(flat_chunks))

    if dry_run:
        logger.info("[DRY RUN] Embeddings non générés.")
        all_embeddings_nested: list[list[list[float]]] = []
        for chunks in all_chunks:
            all_embeddings_nested.append([[0.0] * config.EMBEDDING_DIM] * len(chunks))
    else:
        flat_embeddings = generate_embeddings(flat_chunks)
        # Re-grouper par article
        idx = 0
        all_embeddings_nested = []
        for chunks in all_chunks:
            article_embeddings = flat_embeddings[idx : idx + len(chunks)]
            all_embeddings_nested.append(article_embeddings)
            idx += len(chunks)

    # Upsert dans Qdrant
    loader.ensure_collection(collection_name)
    points_inserted = loader.upsert_points(
        collection=collection_name,
        articles=articles,
        chunks_per_article=all_chunks,
        embeddings_per_article=all_embeddings_nested,
        dry_run=dry_run,
    )
    stats["points"] = points_inserted

    return stats


def process_collection(
    collection_name: str,
    lf_client: LegifranceClient | None,
    loader: QdrantLoader,
    dry_run: bool = False,
    fetch_only: bool = False,
    from_cache: bool = False,
    resume: bool = False,
    el_client: EurlexClient | None = None,
    pdf_client: PdfClient | None = None,
) -> dict:
    """Traiter une collection : fetch articles, embed, upsert."""
    # Étape 1 : obtenir les articles
    if from_cache:
        articles = _load_cache(collection_name)
        if articles is None:
            logger.error(
                "Pas de cache pour '%s'. Lancez d'abord sans --from-cache.",
                collection_name,
            )
            return {"articles": 0, "chunks": 0, "points": 0}
    else:
        articles = _fetch_articles(
            collection_name,
            lf_client,
            resume=resume,
            el_client=el_client,
            pdf_client=pdf_client,
        )
        # Sauvegarder le cache final (filtré + dédupliqué)
        _save_cache(collection_name, articles)

    if fetch_only:
        logger.info("[FETCH ONLY] %d articles cachés, pas d'embeddings.", len(articles))
        return {"articles": len(articles), "chunks": 0, "points": 0}

    # Étape 2 : embed + upsert
    return _embed_and_upsert(collection_name, articles, loader, dry_run)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingestion Legifrance -> Qdrant")
    parser.add_argument(
        "--collection",
        choices=list(config.COLLECTIONS.keys()),
        help="Collection cible (défaut : toutes)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mode test : pas d'insertion ni d'appel OpenAI",
    )
    parser.add_argument(
        "--fetch-only",
        action="store_true",
        help="Fetch Legifrance + cache, pas d'embeddings ni d'upsert",
    )
    parser.add_argument(
        "--from-cache",
        action="store_true",
        help="Utiliser les articles du cache local (pas de fetch Legifrance)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reprendre le fetch depuis le cache partiel (saute les sources déjà récupérées)",
    )
    args = parser.parse_args()

    if args.fetch_only and args.from_cache:
        logger.error("--fetch-only et --from-cache sont mutuellement exclusifs.")
        sys.exit(1)

    if args.resume and args.from_cache:
        logger.error("--resume et --from-cache sont mutuellement exclusifs.")
        sys.exit(1)

    collections = [args.collection] if args.collection else list(config.COLLECTIONS.keys())

    logger.info("=== Ingestion Legifrance -> Qdrant ===")
    logger.info("Collections ciblées : %s", ", ".join(collections))
    if args.dry_run:
        logger.info("MODE DRY-RUN ACTIVÉ")
    if args.fetch_only:
        logger.info("MODE FETCH-ONLY ACTIVÉ (cache uniquement)")
    if args.from_cache:
        logger.info("MODE FROM-CACHE ACTIVÉ (pas de fetch Legifrance)")
    if args.resume:
        logger.info("MODE RESUME ACTIVÉ (reprise depuis le cache partiel)")

    # Le client Legifrance n'est pas nécessaire en mode from-cache
    lf_client = None if args.from_cache else LegifranceClient()
    # EurlexClient : utilisé pour les collections avec eurlex_sources
    el_client = None if args.from_cache else EurlexClient()
    # PdfClient : utilisé pour les collections avec pdf_sources
    pdf_client = None if args.from_cache else PdfClient()
    loader = QdrantLoader()

    start = time.time()
    total_stats = {"articles": 0, "chunks": 0, "points": 0}

    for coll_name in collections:
        logger.info("--- Traitement de '%s' ---", coll_name)
        try:
            stats = process_collection(
                coll_name,
                lf_client,
                loader,
                dry_run=args.dry_run,
                fetch_only=args.fetch_only,
                from_cache=args.from_cache,
                resume=args.resume,
                el_client=el_client,
                pdf_client=pdf_client,
            )
            for k in total_stats:
                total_stats[k] += stats[k]
        except Exception:
            logger.error("Erreur lors du traitement de '%s'", coll_name, exc_info=True)

    elapsed = time.time() - start
    logger.info("=== Résumé ===")
    logger.info("  Articles traités  : %d", total_stats["articles"])
    logger.info("  Chunks générés    : %d", total_stats["chunks"])
    logger.info("  Points insérés    : %d", total_stats["points"])
    logger.info("  Durée totale      : %.1f s", elapsed)


if __name__ == "__main__":
    main()
