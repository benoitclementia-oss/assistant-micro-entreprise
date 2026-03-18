"""Base de données SQLite centralisée pour Assistant Micro-Entreprise."""

import logging
import shutil
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DATA_DIR = _PROJECT_ROOT / "data"
_DB_PATH = _DATA_DIR / "assistant-micro-entreprise.db"
_OLD_CALENDAR_DB = _DATA_DIR / "calendar.db"

_initialized = False


def get_connection() -> sqlite3.Connection:
    """Retourne une connexion SQLite vers la DB centralisée."""
    _ensure_initialized()
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _ensure_initialized() -> None:
    """Initialise la DB si nécessaire (migration + création des tables)."""
    global _initialized
    if _initialized:
        return

    _DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Migration depuis calendar.db si assistant-micro-entreprise.db n'existe pas
    if not _DB_PATH.exists() and _OLD_CALENDAR_DB.exists():
        shutil.copy2(str(_OLD_CALENDAR_DB), str(_DB_PATH))
        logger.info("Migration : calendar.db copié vers assistant-micro-entreprise.db")

    conn = sqlite3.connect(str(_DB_PATH))
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
        logger.info("Base de données initialisée : %s", _DB_PATH)
    finally:
        conn.close()

    _initialized = True


_SCHEMA = """\
-- Table échéances (existante dans calendar.db, créée si absente)
CREATE TABLE IF NOT EXISTS echeances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titre TEXT NOT NULL,
    date TEXT NOT NULL,
    description TEXT DEFAULT '',
    type TEXT DEFAULT 'custom',
    recurrence TEXT DEFAULT NULL,
    fait INTEGER DEFAULT 0
);

-- Profil mono-utilisateur
CREATE TABLE IF NOT EXISTS profil_utilisateur (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    nom TEXT DEFAULT '',
    prenom TEXT DEFAULT '',
    nom_entreprise TEXT DEFAULT '',
    siret TEXT DEFAULT '',
    adresse TEXT DEFAULT '',
    code_postal TEXT DEFAULT '',
    ville TEXT DEFAULT '',
    email TEXT DEFAULT '',
    telephone TEXT DEFAULT '',
    activite TEXT DEFAULT '',
    regime_fiscal TEXT DEFAULT '',
    regime_social TEXT DEFAULT '',
    date_creation_entreprise TEXT DEFAULT '',
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Insérer la ligne unique du profil si absente
INSERT OR IGNORE INTO profil_utilisateur (id) VALUES (1);

-- Faits mémorisés
CREATE TABLE IF NOT EXISTS faits_memoire (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categorie TEXT NOT NULL,
    cle TEXT NOT NULL,
    valeur TEXT NOT NULL,
    source TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(categorie, cle)
);

-- Résumés de sessions
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT DEFAULT (datetime('now')),
    ended_at TEXT DEFAULT NULL,
    resume TEXT DEFAULT '',
    nb_messages INTEGER DEFAULT 0
);
"""
