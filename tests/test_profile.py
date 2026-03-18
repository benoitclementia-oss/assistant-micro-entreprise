"""Tests pour agent/profile.py — CRUD profil utilisateur."""

from agent import profile


class TestConsulterProfil:
    def test_profil_vide_par_defaut(self, mock_db):
        result = profile.consulter_profil()
        assert isinstance(result, dict)
        assert result["id"] == 1
        assert result["nom"] == ""


class TestModifierProfil:
    def test_champs_valides(self, mock_db):
        profile.modifier_profil({"nom": "Dupont", "prenom": "Jean"})
        p = profile.consulter_profil()
        assert p["nom"] == "Dupont"
        assert p["prenom"] == "Jean"

    def test_champs_invalides_ignores(self, mock_db):
        profile.modifier_profil({"champ_inconnu": "valeur", "nom": "Test"})
        p = profile.consulter_profil()
        assert p["nom"] == "Test"
        assert "champ_inconnu" not in p

    def test_updated_at(self, mock_db):
        profile.modifier_profil({"nom": "A"})
        p1 = profile.consulter_profil()
        assert p1["updated_at"] is not None

        profile.modifier_profil({"nom": "B"})
        p2 = profile.consulter_profil()
        assert p2["updated_at"] >= p1["updated_at"]


class TestProfilPourPrompt:
    def test_vide(self, mock_db):
        assert profile.profil_pour_prompt() == ""

    def test_rempli(self, mock_db):
        profile.modifier_profil({"nom": "Dupont", "prenom": "Jean"})
        result = profile.profil_pour_prompt()
        assert "## Profil de l'utilisateur" in result
        assert "Dupont" in result
        assert "Jean" in result


class TestProfilEstVide:
    def test_vide(self, mock_db):
        assert profile.profil_est_vide() is True

    def test_un_champ(self, mock_db):
        profile.modifier_profil({"nom": "Dupont"})
        # 1 champ rempli < 2 → toujours "vide"
        assert profile.profil_est_vide() is True

    def test_deux_champs(self, mock_db):
        profile.modifier_profil({"nom": "Dupont", "prenom": "Jean"})
        assert profile.profil_est_vide() is False


class TestDonneesEmetteur:
    def test_vide(self, mock_db):
        assert profile.donnees_emetteur() == {}

    def test_nom_entreprise(self, mock_db):
        profile.modifier_profil({"nom_entreprise": "SARL Test"})
        result = profile.donnees_emetteur()
        assert result["emetteur_nom"] == "SARL Test"

    def test_fallback_nom_prenom(self, mock_db):
        profile.modifier_profil({"nom": "Dupont", "prenom": "Jean"})
        result = profile.donnees_emetteur()
        assert result["emetteur_nom"] == "Jean Dupont"

    def test_siret(self, mock_db):
        profile.modifier_profil({"siret": "12345678901234"})
        result = profile.donnees_emetteur()
        assert result["emetteur_siret"] == "12345678901234"

    def test_adresse_complete(self, mock_db):
        profile.modifier_profil(
            {
                "adresse": "12 rue de Paris",
                "code_postal": "75001",
                "ville": "Paris",
            }
        )
        result = profile.donnees_emetteur()
        assert "12 rue de Paris" in result["emetteur_adresse"]
        assert "75001 Paris" in result["emetteur_adresse"]
