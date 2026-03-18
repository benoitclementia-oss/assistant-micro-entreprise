"""Tests pour agent/calendar_manager.py — gestion des échéances."""

from datetime import datetime, timedelta

from agent import calendar_manager


class TestInitDb:
    def test_insere_echeances_par_defaut(self, mock_db):
        calendar_manager.init_db()
        conn = mock_db()
        count = conn.execute("SELECT COUNT(*) FROM echeances").fetchone()[0]
        conn.close()
        # 6 échéances prédéfinies + 12 mensuelles = 18
        assert count == 18


class TestAjouterEcheance:
    def test_retourne_un_id(self, mock_db):
        echeance_id = calendar_manager.ajouter_echeance("Test", "2026-06-15", "Description")
        assert isinstance(echeance_id, int)
        assert echeance_id > 0

    def test_stocke_en_db(self, mock_db):
        calendar_manager.ajouter_echeance("Test", "2026-06-15")
        conn = mock_db()
        row = conn.execute("SELECT * FROM echeances WHERE titre = 'Test'").fetchone()
        conn.close()
        assert row is not None
        assert row["date"] == "2026-06-15"


class TestListerEcheances:
    def test_dans_la_plage(self, mock_db):
        tomorrow = (datetime.now().date() + timedelta(days=1)).isoformat()
        calendar_manager.ajouter_echeance("Proche", tomorrow)
        result = calendar_manager.lister_echeances(jours=30)
        titres = [e["titre"] for e in result]
        assert "Proche" in titres

    def test_hors_plage(self, mock_db):
        far = (datetime.now().date() + timedelta(days=365)).isoformat()
        calendar_manager.ajouter_echeance("Lointain", far)
        result = calendar_manager.lister_echeances(jours=30)
        titres = [e["titre"] for e in result]
        assert "Lointain" not in titres


class TestMarquerFait:
    def test_marque_comme_fait(self, mock_db):
        echeance_id = calendar_manager.ajouter_echeance("A faire", "2026-03-01")
        calendar_manager.marquer_fait(echeance_id)

        conn = mock_db()
        row = conn.execute("SELECT fait FROM echeances WHERE id = ?", (echeance_id,)).fetchone()
        conn.close()
        assert row["fait"] == 1
