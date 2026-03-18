"""Tests pour scripts/qdrant_loader.py — génération d'IDs de points."""

import hashlib

from scripts.qdrant_loader import _make_point_id


class TestMakePointId:
    def test_deterministic(self):
        id1 = _make_point_id("LEGIARTI000001", 0)
        id2 = _make_point_id("LEGIARTI000001", 0)
        assert id1 == id2

    def test_different_articles(self):
        id1 = _make_point_id("LEGIARTI000001", 0)
        id2 = _make_point_id("LEGIARTI000002", 0)
        assert id1 != id2

    def test_different_chunks(self):
        id1 = _make_point_id("LEGIARTI000001", 0)
        id2 = _make_point_id("LEGIARTI000001", 1)
        assert id1 != id2

    def test_md5_hex_format(self):
        result = _make_point_id("LEGIARTI000001", 0)
        assert len(result) == 32
        # Vérifier que c'est bien un hex valide
        int(result, 16)

    def test_manual_computation(self):
        """Vérifie que la concaténation article_id + '_' + chunk_index est correcte."""
        raw = "LEGIARTI000001_0"
        expected = hashlib.md5(raw.encode()).hexdigest()
        assert _make_point_id("LEGIARTI000001", 0) == expected
