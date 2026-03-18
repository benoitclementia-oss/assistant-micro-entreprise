"""Tests pour scripts/embedding.py — chunking, estimation de tokens et generate_embeddings."""

from unittest.mock import MagicMock, patch

import pytest
from openai import RateLimitError
from scripts.embedding import (
    BATCH_SIZE,
    CHUNK_SIZE,
    MAX_RETRIES,
    _estimate_tokens,
    _split_into_words,
    chunk_text,
    generate_embeddings,
)


class TestEstimateTokens:
    def test_empty(self):
        assert _estimate_tokens("") == 0

    def test_short(self):
        # 4 chars / 4 = 1 token
        assert _estimate_tokens("test") == 1

    def test_long(self):
        assert _estimate_tokens("a" * 400) == 100

    def test_french_text(self):
        text = "Déclaration de revenus"
        assert _estimate_tokens(text) == len(text) // 4


class TestSplitIntoWords:
    def test_simple(self):
        assert _split_into_words("hello world") == ["hello", " ", "world"]

    def test_multiple_spaces(self):
        assert _split_into_words("hello  world") == ["hello", "  ", "world"]

    def test_newlines(self):
        assert _split_into_words("hello\nworld") == ["hello", "\n", "world"]

    def test_empty(self):
        assert _split_into_words("") == [""]


class TestChunkText:
    def test_short_text_single_chunk(self):
        text = "Texte court."
        chunks = chunk_text(text)
        assert chunks == [text]

    def test_at_limit_single_chunk(self):
        # 800 tokens = 3200 chars, exactement à la limite
        text = "a" * (CHUNK_SIZE * 4)
        assert _estimate_tokens(text) == CHUNK_SIZE
        chunks = chunk_text(text)
        assert len(chunks) == 1

    def test_over_limit_splits(self):
        # "word" = 4 chars → 1 token chacun (len//4)
        text = " ".join(["word"] * 5000)
        assert _estimate_tokens(text) > CHUNK_SIZE
        chunks = chunk_text(text)
        assert len(chunks) > 1

    def test_overlap_present(self):
        """Les chunks consécutifs partagent du contenu (overlap)."""
        words = [f"word{i:04d}" for i in range(2000)]
        text = " ".join(words)
        chunks = chunk_text(text)
        assert len(chunks) >= 2
        # Vérifier le chevauchement : des mots de la fin du chunk 1
        # doivent apparaître au début du chunk 2
        words_end = set(chunks[0].split()[-20:])
        words_start = set(chunks[1].split()[:100])
        shared = words_end & words_start
        assert len(shared) > 0, "Les chunks ne se chevauchent pas"

    def test_empty_string(self):
        chunks = chunk_text("")
        assert chunks == [""]


# ──────────────────────────────────────────────────────────────────
# Tests pour generate_embeddings (avec mock OpenAI)
# ──────────────────────────────────────────────────────────────────


def _make_embedding_response(texts: list[str], dim: int = 8) -> MagicMock:
    """Fabriquer un faux retour OpenAI embeddings.create()."""
    resp = MagicMock()
    items = []
    for i, _t in enumerate(texts):
        item = MagicMock()
        item.embedding = [float(i)] * dim
        items.append(item)
    resp.data = items
    return resp


class TestGenerateEmbeddings:
    @patch("scripts.embedding._client")
    def test_single_text(self, mock_client):
        mock_client.embeddings.create.return_value = _make_embedding_response(["hello"])
        result = generate_embeddings(["hello"])
        assert len(result) == 1
        assert len(result[0]) == 8
        mock_client.embeddings.create.assert_called_once()

    @patch("scripts.embedding._client")
    def test_empty_list(self, mock_client):
        result = generate_embeddings([])
        assert result == []
        mock_client.embeddings.create.assert_not_called()

    @patch("scripts.embedding._client")
    def test_multiple_texts(self, mock_client):
        texts = ["texte un", "texte deux", "texte trois"]
        mock_client.embeddings.create.return_value = _make_embedding_response(texts)
        result = generate_embeddings(texts)
        assert len(result) == 3

    @patch("scripts.embedding._client")
    def test_batching(self, mock_client):
        """Plus de BATCH_SIZE textes → plusieurs appels API."""
        n = BATCH_SIZE + 10
        texts = [f"texte {i}" for i in range(n)]

        def side_effect(**kwargs):
            batch = kwargs["input"]
            return _make_embedding_response(batch)

        mock_client.embeddings.create.side_effect = side_effect
        result = generate_embeddings(texts)
        assert len(result) == n
        assert mock_client.embeddings.create.call_count == 2

    @patch("scripts.embedding._client")
    def test_empty_text_replaced_by_space(self, mock_client):
        """Les textes vides sont remplacés par un espace."""
        texts = ["", "  ", "texte"]
        mock_client.embeddings.create.return_value = _make_embedding_response(texts)
        generate_embeddings(texts)
        call_args = mock_client.embeddings.create.call_args
        batch_sent = call_args.kwargs.get("input") or call_args[1].get("input")
        assert batch_sent[0] == " "
        assert batch_sent[1] == " "
        assert batch_sent[2] == "texte"

    @patch("scripts.embedding.time.sleep")
    @patch("scripts.embedding._client")
    def test_rate_limit_retry(self, mock_client, mock_sleep):
        """RateLimitError → retry avec backoff, puis succès."""
        rate_err = RateLimitError(
            message="rate limit",
            response=MagicMock(status_code=429, headers={}),
            body=None,
        )
        good_response = _make_embedding_response(["texte"])
        mock_client.embeddings.create.side_effect = [rate_err, good_response]

        result = generate_embeddings(["texte"])
        assert len(result) == 1
        mock_sleep.assert_called_once()
        assert mock_client.embeddings.create.call_count == 2

    @patch("scripts.embedding.time.sleep")
    @patch("scripts.embedding._client")
    def test_rate_limit_max_retries_raises(self, mock_client, mock_sleep):
        """MAX_RETRIES atteint → exception propagée."""
        rate_err = RateLimitError(
            message="rate limit",
            response=MagicMock(status_code=429, headers={}),
            body=None,
        )
        mock_client.embeddings.create.side_effect = [rate_err] * MAX_RETRIES

        with pytest.raises(RateLimitError):
            generate_embeddings(["texte"])
        assert mock_client.embeddings.create.call_count == MAX_RETRIES

    @patch("scripts.embedding._client")
    def test_preserves_order(self, mock_client):
        """Les embeddings sont dans le même ordre que les textes d'entrée."""
        texts = ["alpha", "beta", "gamma"]

        def side_effect(**kwargs):
            resp = MagicMock()
            items = []
            for i, _t in enumerate(kwargs["input"]):
                item = MagicMock()
                item.embedding = [float(i + 1)]
                items.append(item)
            resp.data = items
            return resp

        mock_client.embeddings.create.side_effect = side_effect
        result = generate_embeddings(texts)
        assert result == [[1.0], [2.0], [3.0]]

    @patch("scripts.embedding._client")
    def test_model_parameter(self, mock_client):
        """Vérifie que le bon modèle est passé à l'API."""
        mock_client.embeddings.create.return_value = _make_embedding_response(["t"])
        generate_embeddings(["t"])
        call_kwargs = mock_client.embeddings.create.call_args.kwargs
        assert call_kwargs["model"] == "text-embedding-3-small"
