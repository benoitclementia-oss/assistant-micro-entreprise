"""Generation d'embeddings via OpenAI text-embedding-3-small."""

import logging
import re
import time

from openai import OpenAI, RateLimitError

from . import config

logger = logging.getLogger(__name__)

_client = OpenAI(api_key=config.OPENAI_API_KEY)

# Parametres de chunking
CHUNK_SIZE = 800  # tokens approximatifs
CHUNK_OVERLAP = 100
BATCH_SIZE = 100  # textes par appel API


def _estimate_tokens(text: str) -> int:
    """Estimation grossiere : ~1 token pour 4 caracteres en francais."""
    return len(text) // 4


def _split_into_words(text: str) -> list[str]:
    """Decouper un texte en mots (espaces, retours a la ligne)."""
    return re.split(r"(\s+)", text)


def chunk_text(text: str) -> list[str]:
    """Decouper un texte long en chunks avec chevauchement.

    Retourne une liste de chunks. Si le texte est court, retourne [text].
    """
    if _estimate_tokens(text) <= CHUNK_SIZE:
        return [text]

    words = _split_into_words(text)
    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for word in words:
        word_tokens = _estimate_tokens(word)
        if current_tokens + word_tokens > CHUNK_SIZE and current:
            chunk = "".join(current).strip()
            if chunk:
                chunks.append(chunk)
            # Chevauchement : garder les derniers mots
            overlap_chars = CHUNK_OVERLAP * 4
            overlap_text = "".join(current)
            overlap_part = (
                overlap_text[-overlap_chars:] if len(overlap_text) > overlap_chars else overlap_text
            )
            current = [overlap_part]
            current_tokens = _estimate_tokens(overlap_part)
        current.append(word)
        current_tokens += word_tokens

    if current:
        chunk = "".join(current).strip()
        if chunk:
            chunks.append(chunk)

    return chunks if chunks else [text]


MAX_RETRIES = 5
BACKOFF_FACTOR = 2


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generer les embeddings pour une liste de textes, par batch."""
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        # Nettoyer les textes vides
        batch = [t if t.strip() else " " for t in batch]

        logger.debug(
            "Embedding batch %d-%d / %d",
            i + 1,
            min(i + BATCH_SIZE, len(texts)),
            len(texts),
        )

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = _client.embeddings.create(
                    model=config.EMBEDDING_MODEL,
                    input=batch,
                )
                break
            except RateLimitError as exc:
                if attempt == MAX_RETRIES:
                    raise
                wait = BACKOFF_FACTOR**attempt
                logger.warning(
                    "Rate limit OpenAI (batch %d-%d, tentative %d/%d) — attente %ds : %s",
                    i + 1,
                    min(i + BATCH_SIZE, len(texts)),
                    attempt,
                    MAX_RETRIES,
                    wait,
                    exc,
                )
                time.sleep(wait)

        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)

    return all_embeddings
