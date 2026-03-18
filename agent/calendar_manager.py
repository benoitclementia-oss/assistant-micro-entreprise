"""Gestion du calendrier des échéances (SQLite local)."""

import logging
from datetime import datetime, timedelta

from . import database

logger = logging.getLogger(__name__)

# Échéances fiscales et sociales pré-remplies pour micro-entreprises.
# Les dates utilisent l'année courante ; les récurrentes seront dupliquées
# chaque année au besoin.
_ECHEANCES_DEFAUT = [
    {
        "titre": "Déclaration de revenus annuelle",
        "date_mois_jour": "05-25",
        "description": "Déclaration annuelle des revenus (formulaire 2042-C-PRO).",
        "type": "fiscal",
        "recurrence": "annuel",
    },
    {
        "titre": "CFE — Cotisation Foncière des Entreprises",
        "date_mois_jour": "12-15",
        "description": "Paiement de la CFE avant le 15 décembre.",
        "type": "fiscal",
        "recurrence": "annuel",
    },
    {
        "titre": "Déclaration CA trimestrielle URSSAF — T1",
        "date_mois_jour": "04-30",
        "description": "Déclaration trimestrielle du CA (janvier-mars).",
        "type": "social",
        "recurrence": "trimestriel",
    },
    {
        "titre": "Déclaration CA trimestrielle URSSAF — T2",
        "date_mois_jour": "07-31",
        "description": "Déclaration trimestrielle du CA (avril-juin).",
        "type": "social",
        "recurrence": "trimestriel",
    },
    {
        "titre": "Déclaration CA trimestrielle URSSAF — T3",
        "date_mois_jour": "10-31",
        "description": "Déclaration trimestrielle du CA (juillet-septembre).",
        "type": "social",
        "recurrence": "trimestriel",
    },
    {
        "titre": "Déclaration CA trimestrielle URSSAF — T4",
        "date_mois_jour": "01-31",
        "description": "Déclaration trimestrielle du CA (octobre-décembre).",
        "type": "social",
        "recurrence": "trimestriel",
    },
]


_db_initialized = False


def init_db() -> None:
    """Insère les échéances par défaut si la table est vide."""
    global _db_initialized
    if _db_initialized:
        return
    conn = database.get_connection()
    try:
        count = conn.execute("SELECT COUNT(*) FROM echeances").fetchone()[0]
        if count == 0:
            year = datetime.now().year
            inserted = 0

            for e in _ECHEANCES_DEFAUT:
                date_str = f"{year}-{e['date_mois_jour']}"
                conn.execute(
                    "INSERT INTO echeances (titre, date, description, type, recurrence) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (e["titre"], date_str, e["description"], e["type"], e["recurrence"]),
                )
                inserted += 1

            import calendar as cal_mod

            for month in range(1, 13):
                last_day = cal_mod.monthrange(year, month)[1]
                date_str = f"{year}-{month:02d}-{last_day:02d}"
                mois_noms = [
                    "",
                    "janvier",
                    "février",
                    "mars",
                    "avril",
                    "mai",
                    "juin",
                    "juillet",
                    "août",
                    "septembre",
                    "octobre",
                    "novembre",
                    "décembre",
                ]
                conn.execute(
                    "INSERT INTO echeances (titre, date, description, type, recurrence) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        f"Déclaration CA mensuelle URSSAF — {mois_noms[month]}",
                        date_str,
                        f"Déclaration mensuelle du CA ({mois_noms[month]} {year}).",
                        "social",
                        "mensuel",
                    ),
                )
                inserted += 1

            logger.info("Échéances par défaut insérées (%d)", inserted)

        conn.commit()
        _db_initialized = True
    finally:
        conn.close()


def lister_echeances(jours: int = 30) -> list[dict]:
    """Liste les échéances non faites dans les N prochains jours."""
    init_db()
    today = datetime.now().date()
    horizon = today + timedelta(days=jours)

    conn = database.get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM echeances WHERE date BETWEEN ? AND ? ORDER BY date ASC",
            (today.isoformat(), horizon.isoformat()),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def ajouter_echeance(
    titre: str,
    date: str,
    description: str = "",
    type_echeance: str = "custom",
) -> int:
    """Ajoute une échéance et retourne son ID."""
    init_db()
    conn = database.get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO echeances (titre, date, description, type) VALUES (?, ?, ?, ?)",
            (titre, date, description, type_echeance),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def marquer_fait(echeance_id: int) -> None:
    """Marque une échéance comme faite."""
    init_db()
    conn = database.get_connection()
    try:
        conn.execute(
            "UPDATE echeances SET fait = 1 WHERE id = ?",
            (echeance_id,),
        )
        conn.commit()
    finally:
        conn.close()
