"""Mémoire inter-session : faits mémorisés et résumés de sessions."""

import logging
from datetime import datetime

from openai import OpenAI
from scripts import config

from . import database

logger = logging.getLogger(__name__)


# --- Faits mémorisés ---


def memoriser(categorie: str, cle: str, valeur: str, source: str = "") -> dict:
    """Mémorise ou met à jour un fait (upsert sur categorie+cle)."""
    conn = database.get_connection()
    try:
        conn.execute(
            "INSERT INTO faits_memoire (categorie, cle, valeur, source, updated_at) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(categorie, cle) DO UPDATE SET "
            "valeur = excluded.valeur, source = excluded.source, "
            "updated_at = excluded.updated_at",
            (categorie, cle, valeur, source, datetime.now().isoformat()),
        )
        conn.commit()
        logger.info("Fait mémorisé : [%s] %s = %s", categorie, cle, valeur)
    finally:
        conn.close()

    return {"categorie": categorie, "cle": cle, "valeur": valeur}


def rappeler(categorie: str | None = None, query: str = "") -> list[dict]:
    """Recherche dans les faits mémorisés."""
    conn = database.get_connection()
    try:
        if categorie and query:
            rows = conn.execute(
                "SELECT categorie, cle, valeur, source, updated_at "
                "FROM faits_memoire "
                "WHERE categorie = ? AND (cle LIKE ? OR valeur LIKE ?) "
                "ORDER BY updated_at DESC",
                (categorie, f"%{query}%", f"%{query}%"),
            ).fetchall()
        elif categorie:
            rows = conn.execute(
                "SELECT categorie, cle, valeur, source, updated_at "
                "FROM faits_memoire WHERE categorie = ? "
                "ORDER BY updated_at DESC",
                (categorie,),
            ).fetchall()
        elif query:
            rows = conn.execute(
                "SELECT categorie, cle, valeur, source, updated_at "
                "FROM faits_memoire "
                "WHERE cle LIKE ? OR valeur LIKE ? "
                "ORDER BY updated_at DESC",
                (f"%{query}%", f"%{query}%"),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT categorie, cle, valeur, source, updated_at "
                "FROM faits_memoire ORDER BY updated_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def tous_les_faits() -> list[dict]:
    """Retourne tous les faits mémorisés (pour le system prompt)."""
    return rappeler()


def faits_pour_prompt() -> str:
    """Formate tous les faits mémorisés pour le system prompt."""
    faits = tous_les_faits()
    if not faits:
        return ""

    lines = ["## Faits mémorisés"]
    par_cat: dict[str, list] = {}
    for f in faits:
        par_cat.setdefault(f["categorie"], []).append(f)

    for cat, items in sorted(par_cat.items()):
        lines.append(f"### {cat}")
        for item in items:
            lines.append(f"- **{item['cle']}** : {item['valeur']}")

    return "\n".join(lines)


# --- Sessions ---


def start_session() -> int:
    """Démarre une nouvelle session et retourne son ID."""
    conn = database.get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO sessions (started_at, nb_messages) VALUES (?, 0)",
            (datetime.now().isoformat(),),
        )
        conn.commit()
        session_id = cursor.lastrowid
        logger.info("Session démarrée : %d", session_id)
        return session_id
    finally:
        conn.close()


def close_session(session_id: int, messages: list[dict], client: OpenAI | None = None) -> None:
    """Ferme une session : compte les messages et génère un résumé via GPT-4o."""
    # Compter les messages utilisateur
    user_messages = [m for m in messages if m.get("role") == "user"]
    nb = len(user_messages)

    if nb == 0:
        # Pas de conversation, pas de résumé
        conn = database.get_connection()
        try:
            conn.execute(
                "UPDATE sessions SET ended_at = ?, nb_messages = 0 WHERE id = ?",
                (datetime.now().isoformat(), session_id),
            )
            conn.commit()
        finally:
            conn.close()
        return

    # Générer un résumé via GPT-4o
    resume = _generer_resume(messages, client)

    conn = database.get_connection()
    try:
        conn.execute(
            "UPDATE sessions SET ended_at = ?, resume = ?, nb_messages = ? WHERE id = ?",
            (datetime.now().isoformat(), resume, nb, session_id),
        )
        conn.commit()
        logger.info("Session %d fermée (%d messages)", session_id, nb)
    finally:
        conn.close()


def sessions_recentes(n: int = 3) -> list[dict]:
    """Retourne les N dernières sessions avec résumé."""
    conn = database.get_connection()
    try:
        rows = conn.execute(
            "SELECT id, started_at, ended_at, resume, nb_messages "
            "FROM sessions WHERE resume != '' "
            "ORDER BY id DESC LIMIT ?",
            (n,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def sessions_pour_prompt() -> str:
    """Formate les sessions récentes pour le system prompt."""
    sessions = sessions_recentes(3)
    if not sessions:
        return ""

    lines = ["## Sessions précédentes"]
    for s in reversed(sessions):  # chronologique
        date = s["started_at"][:10] if s["started_at"] else "?"
        lines.append(f"### Session du {date} ({s['nb_messages']} messages)")
        lines.append(s["resume"])

    return "\n".join(lines)


def _generer_resume(messages: list[dict], client: OpenAI | None = None) -> str:
    """Génère un résumé de conversation via GPT-4o."""
    if client is None:
        client = OpenAI(api_key=config.OPENAI_API_KEY)

    # Extraire les messages user/assistant pour le résumé
    conversation = []
    for m in messages:
        role = m.get("role", "")
        content = m.get("content", "")
        if role in ("user", "assistant") and content:
            conversation.append(f"{role}: {content[:500]}")

    if not conversation:
        return ""

    texte_conv = "\n".join(conversation[-20:])  # max 20 derniers échanges

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Résume cette conversation en 2-3 phrases concises. "
                        "Mentionne les sujets abordés, les actions effectuées "
                        "et les décisions prises. Réponds en français."
                    ),
                },
                {"role": "user", "content": texte_conv},
            ],
            max_tokens=200,
        )
        return response.choices[0].message.content or ""
    except Exception:
        logger.exception("Erreur lors de la génération du résumé de session")
        return "(résumé indisponible)"
