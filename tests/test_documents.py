"""Tests pour agent/documents.py — workflow brouillon/confirmation."""

from unittest.mock import MagicMock

import pytest
from agent import documents


@pytest.fixture(autouse=True)
def mock_jinja(monkeypatch):
    """Mock le moteur de templates Jinja2."""
    mock_tmpl = MagicMock()
    mock_tmpl.render.return_value = "Contenu du document rendu"

    mock_env = MagicMock()
    mock_env.get_template.return_value = mock_tmpl

    monkeypatch.setattr(documents, "_env", mock_env)
    return mock_tmpl


# --- preparer_document ---


class TestPreparerDocument:
    def test_facture_basique(self, mock_jinja):
        result = documents.preparer_document("facture", {"numero": "F001"})
        assert "draft_id" in result
        assert "contenu" in result
        assert result["type"] == "facture"

    def test_calcul_total_auto(self, mock_jinja):
        donnees = {
            "numero": "F001",
            "prestations": [
                {"description": "Service A", "quantite": 2, "prix_unitaire": 100},
                {"description": "Service B", "quantite": 1, "prix_unitaire": 50},
            ],
        }
        result = documents.preparer_document("facture", donnees)
        draft = documents._drafts[result["draft_id"]]
        assert draft["donnees"]["total"] == 250

    def test_date_auto(self, mock_jinja):
        result = documents.preparer_document("facture", {"numero": "F001"})
        draft = documents._drafts[result["draft_id"]]
        assert "date" in draft["donnees"]
        assert "/" in draft["donnees"]["date"]  # format JJ/MM/AAAA

    def test_devis(self, mock_jinja):
        result = documents.preparer_document("devis", {"numero": "D001"})
        assert result["type"] == "devis"

    def test_types_valides(self, mock_jinja):
        for t in documents.VALID_TYPES:
            result = documents.preparer_document(t, {"numero": "X001"})
            assert result["type"] == t

    def test_type_invalide(self):
        with pytest.raises(ValueError, match="Type de document invalide"):
            documents.preparer_document("contrat", {})

    def test_draft_stocke_en_memoire(self, mock_jinja):
        result = documents.preparer_document("facture", {"numero": "F001"})
        assert result["draft_id"] in documents._drafts

    def test_total_avec_quantite_implicite(self, mock_jinja):
        """quantite absente → défaut 1."""
        donnees = {
            "prestations": [{"description": "X", "prix_unitaire": 75}],
        }
        result = documents.preparer_document("facture", donnees)
        draft = documents._drafts[result["draft_id"]]
        assert draft["donnees"]["total"] == 75


# --- confirmer_document ---


class TestConfirmerDocument:
    def test_sauvegarde_fichier(self, mock_jinja, tmp_output_dir):
        result = documents.preparer_document("facture", {"numero": "F001"})
        path = documents.confirmer_document(result["draft_id"])
        assert tmp_output_dir.exists()
        assert (tmp_output_dir / "facture_F001.md").exists()
        assert str(tmp_output_dir) in path

    def test_supprime_draft(self, mock_jinja, tmp_output_dir):
        result = documents.preparer_document("facture", {"numero": "F001"})
        draft_id = result["draft_id"]
        documents.confirmer_document(draft_id)
        assert draft_id not in documents._drafts

    def test_draft_inconnu(self):
        with pytest.raises(ValueError, match="Brouillon introuvable"):
            documents.confirmer_document("inexistant")

    def test_double_confirmation(self, mock_jinja, tmp_output_dir):
        result = documents.preparer_document("facture", {"numero": "F001"})
        documents.confirmer_document(result["draft_id"])
        with pytest.raises(ValueError):
            documents.confirmer_document(result["draft_id"])

    def test_nom_fichier_avec_reference(self, mock_jinja, tmp_output_dir):
        result = documents.preparer_document("confirmation", {"reference": "REF-42"})
        documents.confirmer_document(result["draft_id"])
        assert (tmp_output_dir / "confirmation_REF-42.md").exists()


# --- lister_documents ---


class TestListerDocuments:
    def test_dossier_vide(self, tmp_output_dir):
        tmp_output_dir.mkdir(parents=True, exist_ok=True)
        result = documents.lister_documents()
        assert result == []

    def test_apres_sauvegarde(self, mock_jinja, tmp_output_dir):
        result = documents.preparer_document("facture", {"numero": "F001"})
        documents.confirmer_document(result["draft_id"])
        docs = documents.lister_documents()
        assert len(docs) == 1
        assert docs[0]["fichier"] == "facture_F001.md"
