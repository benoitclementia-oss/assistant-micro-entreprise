"""Fixtures partagées pour les tests Assistant Micro-Entreprise."""

import os

# IMPORTANT : définir les variables d'environnement AVANT tout import
# de scripts/config.py (qui exécute _require() au niveau module).
os.environ.setdefault("LEGIFRANCE_CLIENT_ID", "test_id")
os.environ.setdefault("LEGIFRANCE_CLIENT_SECRET", "test_secret")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-key")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")

import sqlite3

import pytest
from agent import database


@pytest.fixture
def mock_db(tmp_path, monkeypatch):
    """DB SQLite temporaire avec le vrai schéma."""
    db_path = tmp_path / "test.db"

    init_conn = sqlite3.connect(str(db_path))
    init_conn.executescript(database._SCHEMA)
    init_conn.commit()
    init_conn.close()

    def _get_connection():
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    monkeypatch.setattr(database, "get_connection", _get_connection)

    from agent import calendar_manager

    monkeypatch.setattr(calendar_manager, "_db_initialized", False)

    return _get_connection


@pytest.fixture
def tmp_output_dir(tmp_path, monkeypatch):
    """Redirige la sortie documents vers un dossier temporaire."""
    from agent import documents

    out = tmp_path / "documents"
    monkeypatch.setattr(documents, "_OUTPUT_DIR", out)
    return out


@pytest.fixture(autouse=True)
def _clear_drafts():
    """Vide les brouillons entre chaque test."""
    from agent import documents

    documents._drafts.clear()
    yield
    documents._drafts.clear()
