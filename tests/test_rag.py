"""Tests pour agent/rag.py — search et format_context."""

from unittest.mock import MagicMock, patch

from agent.rag import ALL_COLLECTIONS, format_context, search


class TestFormatContext:
    def test_vide(self):
        result = format_context([])
        assert result == "Aucun résultat trouvé dans la base juridique."

    def test_un_resultat(self):
        results = [
            {
                "titre": "Article 293 B du CGI",
                "code_source": "Code général des impôts",
                "article_id": "LEGIARTI000006309445",
                "texte": "Contenu de l'article.",
            }
        ]
        result = format_context(results)
        assert "[1] Article 293 B du CGI" in result
        assert "Code général des impôts" in result
        assert "LEGIARTI000006309445" in result
        assert "Contenu de l'article." in result

    def test_plusieurs_resultats(self):
        results = [
            {
                "titre": "Art. 1",
                "code_source": "CGI",
                "article_id": "ID1",
                "texte": "Texte 1",
            },
            {
                "titre": "Art. 2",
                "code_source": "LPF",
                "article_id": "ID2",
                "texte": "Texte 2",
            },
        ]
        result = format_context(results)
        assert "[1] Art. 1" in result
        assert "[2] Art. 2" in result
        assert "\n\n---\n\n" in result

    def test_code_source_vide(self):
        results = [
            {
                "titre": "Article",
                "code_source": "",
                "article_id": "ID1",
                "texte": "Texte",
            }
        ]
        result = format_context(results)
        # Pas de " — " quand code_source est vide
        assert " — " not in result.split("\n")[0]


# ──────────────────────────────────────────────────────────────────
# Helpers pour mocker Qdrant
# ──────────────────────────────────────────────────────────────────


def _make_hit(score: float, payload: dict) -> MagicMock:
    """Fabriquer un faux point Qdrant."""
    hit = MagicMock()
    hit.score = score
    hit.payload = payload
    return hit


def _make_query_response(hits: list) -> MagicMock:
    """Fabriquer un faux retour query_points."""
    resp = MagicMock()
    resp.points = hits
    return resp


# ──────────────────────────────────────────────────────────────────
# Tests pour search() — avec mock Qdrant + mock embeddings
# ──────────────────────────────────────────────────────────────────


class TestSearch:
    @patch("agent.rag.generate_embeddings", return_value=[[0.1] * 1536])
    @patch("agent.rag._qdrant")
    def test_recherche_basique(self, mock_qdrant, mock_embed):
        """Un résultat trouvé dans une collection."""
        hit = _make_hit(
            0.85,
            {
                "article_id": "LEGIARTI000001",
                "titre": "Article 293 B",
                "texte": "Franchise en base de TVA.",
                "code_source": "CGI",
                "chunk_index": 0,
            },
        )
        mock_qdrant.query_points.return_value = _make_query_response([hit])

        results = search("TVA micro-entreprise", collections=["lois_fiscales"])
        assert len(results) == 1
        assert results[0]["score"] == 0.85
        assert results[0]["article_id"] == "LEGIARTI000001"
        assert results[0]["collection"] == "lois_fiscales"

    @patch("agent.rag.generate_embeddings", return_value=[[0.1] * 1536])
    @patch("agent.rag._qdrant")
    def test_recherche_vide(self, mock_qdrant, mock_embed):
        """Aucun résultat."""
        mock_qdrant.query_points.return_value = _make_query_response([])
        results = search("requête sans résultat", collections=["lois_fiscales"])
        assert results == []

    @patch("agent.rag.generate_embeddings", return_value=[[0.1] * 1536])
    @patch("agent.rag._qdrant")
    def test_toutes_collections_par_defaut(self, mock_qdrant, mock_embed):
        """Sans paramètre collections, toutes les collections sont interrogées."""
        mock_qdrant.query_points.return_value = _make_query_response([])
        search("test")
        assert mock_qdrant.query_points.call_count == len(ALL_COLLECTIONS)

    @patch("agent.rag.generate_embeddings", return_value=[[0.1] * 1536])
    @patch("agent.rag._qdrant")
    def test_collection_inconnue_ignoree(self, mock_qdrant, mock_embed):
        """Une collection inconnue est ignorée sans erreur."""
        mock_qdrant.query_points.return_value = _make_query_response([])
        results = search("test", collections=["collection_inexistante"])
        assert results == []
        mock_qdrant.query_points.assert_not_called()

    @patch("agent.rag.generate_embeddings", return_value=[[0.1] * 1536])
    @patch("agent.rag._qdrant")
    def test_tri_par_score_decroissant(self, mock_qdrant, mock_embed):
        """Les résultats sont triés par score décroissant."""
        hits_col1 = [
            _make_hit(
                0.70,
                {
                    "article_id": "A1",
                    "titre": "T1",
                    "texte": "X",
                    "code_source": "C1",
                    "chunk_index": 0,
                },
            ),
            _make_hit(
                0.90,
                {
                    "article_id": "A2",
                    "titre": "T2",
                    "texte": "X",
                    "code_source": "C1",
                    "chunk_index": 0,
                },
            ),
        ]
        hits_col2 = [
            _make_hit(
                0.80,
                {
                    "article_id": "A3",
                    "titre": "T3",
                    "texte": "X",
                    "code_source": "C2",
                    "chunk_index": 0,
                },
            ),
        ]

        def side_effect(collection_name, **kwargs):
            if collection_name == "lois_fiscales":
                return _make_query_response(hits_col1)
            return _make_query_response(hits_col2)

        mock_qdrant.query_points.side_effect = side_effect
        results = search("test", collections=["lois_fiscales", "regles_comptables"])

        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)
        assert scores[0] == 0.90

    @patch("agent.rag.generate_embeddings", return_value=[[0.1] * 1536])
    @patch("agent.rag._qdrant")
    def test_top_k_limite(self, mock_qdrant, mock_embed):
        """Le résultat est limité à top_k éléments."""
        hits = [
            _make_hit(
                0.9 - i * 0.1,
                {
                    "article_id": f"A{i}",
                    "titre": f"T{i}",
                    "texte": "X",
                    "code_source": "C",
                    "chunk_index": 0,
                },
            )
            for i in range(5)
        ]
        mock_qdrant.query_points.return_value = _make_query_response(hits)
        results = search("test", collections=["lois_fiscales"], top_k=3)
        assert len(results) == 3

    @patch("agent.rag.generate_embeddings", return_value=[[0.1] * 1536])
    @patch("agent.rag._qdrant")
    def test_erreur_qdrant_continue(self, mock_qdrant, mock_embed):
        """Une erreur Qdrant sur une collection n'empêche pas les autres."""
        mock_qdrant.query_points.side_effect = [
            Exception("Qdrant down"),
            _make_query_response(
                [
                    _make_hit(
                        0.8,
                        {
                            "article_id": "A1",
                            "titre": "T",
                            "texte": "X",
                            "code_source": "C",
                            "chunk_index": 0,
                        },
                    ),
                ]
            ),
        ]
        results = search("test", collections=["lois_fiscales", "regles_comptables"])
        assert len(results) == 1
        assert results[0]["collection"] == "regles_comptables"

    @patch("agent.rag.generate_embeddings", return_value=[[0.1] * 1536])
    @patch("agent.rag._qdrant")
    def test_payload_vide(self, mock_qdrant, mock_embed):
        """Un hit sans payload retourne des valeurs par défaut."""
        hit = MagicMock()
        hit.score = 0.5
        hit.payload = None
        mock_qdrant.query_points.return_value = _make_query_response([hit])

        results = search("test", collections=["lois_fiscales"])
        assert len(results) == 1
        assert results[0]["article_id"] == ""
        assert results[0]["titre"] == ""
        assert results[0]["chunk_index"] == 0

    @patch("agent.rag.generate_embeddings", return_value=[[0.1] * 1536])
    @patch("agent.rag._qdrant")
    def test_multi_collection_merge(self, mock_qdrant, mock_embed):
        """Les résultats de plusieurs collections sont fusionnés."""

        def side_effect(collection_name, **kwargs):
            hit = _make_hit(
                0.75,
                {
                    "article_id": f"ID-{collection_name}",
                    "titre": f"Art-{collection_name}",
                    "texte": "Contenu",
                    "code_source": collection_name,
                    "chunk_index": 0,
                },
            )
            return _make_query_response([hit])

        mock_qdrant.query_points.side_effect = side_effect
        results = search("test", collections=["lois_fiscales", "regles_comptables"], top_k=10)
        assert len(results) == 2
        collections = {r["collection"] for r in results}
        assert collections == {"lois_fiscales", "regles_comptables"}
