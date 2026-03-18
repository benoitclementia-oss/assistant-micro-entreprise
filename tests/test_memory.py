"""Tests pour agent/memory.py — faits mémorisés et sessions."""

from unittest.mock import MagicMock

from agent import memory

# --- memoriser ---


class TestMemoriser:
    def test_insertion(self, mock_db):
        result = memory.memoriser("fiscal", "taux_tva", "20%")
        assert result == {"categorie": "fiscal", "cle": "taux_tva", "valeur": "20%"}

        faits = memory.rappeler()
        assert len(faits) == 1
        assert faits[0]["valeur"] == "20%"

    def test_upsert_existant(self, mock_db):
        memory.memoriser("fiscal", "taux_tva", "20%")
        memory.memoriser("fiscal", "taux_tva", "5.5%")

        faits = memory.rappeler()
        assert len(faits) == 1
        assert faits[0]["valeur"] == "5.5%"

    def test_categories_differentes(self, mock_db):
        memory.memoriser("fiscal", "tva", "20%")
        memory.memoriser("clients", "principal", "Acme Corp")

        faits = memory.rappeler()
        assert len(faits) == 2


# --- rappeler ---


class TestRappeler:
    def test_tous(self, mock_db):
        memory.memoriser("a", "k1", "v1")
        memory.memoriser("b", "k2", "v2")
        assert len(memory.rappeler()) == 2

    def test_par_categorie(self, mock_db):
        memory.memoriser("fiscal", "tva", "20%")
        memory.memoriser("clients", "nom", "Acme")

        result = memory.rappeler(categorie="fiscal")
        assert len(result) == 1
        assert result[0]["categorie"] == "fiscal"

    def test_par_query(self, mock_db):
        memory.memoriser("fiscal", "taux_tva", "20%")
        memory.memoriser("fiscal", "regime", "micro-BNC")

        result = memory.rappeler(query="tva")
        assert len(result) == 1
        assert "tva" in result[0]["cle"]

    def test_categorie_et_query(self, mock_db):
        memory.memoriser("fiscal", "taux_tva", "20%")
        memory.memoriser("fiscal", "regime", "micro-BNC")
        memory.memoriser("clients", "tva_client", "intra")

        result = memory.rappeler(categorie="fiscal", query="tva")
        assert len(result) == 1
        assert result[0]["cle"] == "taux_tva"

    def test_aucun_resultat(self, mock_db):
        assert memory.rappeler(query="inexistant") == []


# --- faits_pour_prompt ---


class TestFaitsPourPrompt:
    def test_vide(self, mock_db):
        assert memory.faits_pour_prompt() == ""

    def test_formate_avec_headers(self, mock_db):
        memory.memoriser("fiscal", "tva", "20%")
        memory.memoriser("clients", "principal", "Acme")

        result = memory.faits_pour_prompt()
        assert "## Faits mémorisés" in result
        assert "### fiscal" in result or "### clients" in result
        assert "20%" in result
        assert "Acme" in result


# --- Sessions ---


class TestSessions:
    def test_start_session(self, mock_db):
        session_id = memory.start_session()
        assert isinstance(session_id, int)
        assert session_id > 0

    def test_close_session_sans_messages(self, mock_db):
        session_id = memory.start_session()
        memory.close_session(session_id, messages=[])
        # Pas d'erreur, session fermée avec 0 messages

    def test_close_session_avec_messages(self, mock_db):
        session_id = memory.start_session()

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Résumé de test"))]
        mock_client.chat.completions.create.return_value = mock_response

        messages = [
            {"role": "user", "content": "Bonjour"},
            {"role": "assistant", "content": "Salut !"},
        ]
        memory.close_session(session_id, messages, client=mock_client)

        sessions = memory.sessions_recentes(1)
        assert len(sessions) == 1
        assert sessions[0]["resume"] == "Résumé de test"
        assert sessions[0]["nb_messages"] == 1  # 1 message user

    def test_sessions_pour_prompt(self, mock_db):
        session_id = memory.start_session()

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Résumé"))]
        )

        messages = [
            {"role": "user", "content": "Test"},
            {"role": "assistant", "content": "OK"},
        ]
        memory.close_session(session_id, messages, client=mock_client)

        result = memory.sessions_pour_prompt()
        assert "## Sessions précédentes" in result
        assert "Résumé" in result
