"""Gestion du profil utilisateur (mono-utilisateur)."""

import logging
from datetime import datetime

from . import database

logger = logging.getLogger(__name__)

CHAMPS_PROFIL = [
    "nom",
    "prenom",
    "nom_entreprise",
    "siret",
    "adresse",
    "code_postal",
    "ville",
    "email",
    "telephone",
    "activite",
    "regime_fiscal",
    "regime_social",
    "date_creation_entreprise",
]


def consulter_profil() -> dict:
    """Retourne le profil utilisateur complet."""
    conn = database.get_connection()
    try:
        row = conn.execute("SELECT * FROM profil_utilisateur WHERE id = 1").fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


def modifier_profil(champs: dict) -> dict:
    """Met à jour les champs du profil. Retourne le profil mis à jour."""
    valides = {k: v for k, v in champs.items() if k in CHAMPS_PROFIL}
    if not valides:
        return consulter_profil()

    sets = ", ".join(f"{k} = ?" for k in valides)
    sets += ", updated_at = ?"
    values = list(valides.values()) + [datetime.now().isoformat()]

    conn = database.get_connection()
    try:
        conn.execute(
            f"UPDATE profil_utilisateur SET {sets} WHERE id = 1",
            values,
        )
        conn.commit()
        logger.info("Profil mis à jour : %s", list(valides.keys()))
    finally:
        conn.close()

    return consulter_profil()


def profil_pour_prompt() -> str:
    """Formate le profil pour injection dans le system prompt."""
    profil = consulter_profil()
    remplis = {k: v for k, v in profil.items() if k in CHAMPS_PROFIL and v}
    if not remplis:
        return ""

    labels = {
        "nom": "Nom",
        "prenom": "Prénom",
        "nom_entreprise": "Entreprise",
        "siret": "SIRET",
        "adresse": "Adresse",
        "code_postal": "Code postal",
        "ville": "Ville",
        "email": "Email",
        "telephone": "Téléphone",
        "activite": "Activité",
        "regime_fiscal": "Régime fiscal",
        "regime_social": "Régime social",
        "date_creation_entreprise": "Date création entreprise",
    }
    lines = ["## Profil de l'utilisateur"]
    for k, v in remplis.items():
        label = labels.get(k, k)
        lines.append(f"- **{label}** : {v}")
    return "\n".join(lines)


def profil_est_vide() -> bool:
    """Vérifie si le profil est essentiellement vide."""
    profil = consulter_profil()
    remplis = sum(1 for k in CHAMPS_PROFIL if profil.get(k))
    return remplis < 2


def donnees_emetteur() -> dict:
    """Retourne les champs émetteur pour pré-remplir les documents."""
    profil = consulter_profil()
    result = {}
    if profil.get("nom_entreprise") or profil.get("nom"):
        nom = (
            profil.get("nom_entreprise")
            or f"{profil.get('prenom', '')} {profil.get('nom', '')}".strip()
        )
        result["emetteur_nom"] = nom
    if profil.get("siret"):
        result["emetteur_siret"] = profil["siret"]

    parts = []
    if profil.get("adresse"):
        parts.append(profil["adresse"])
    if profil.get("code_postal") or profil.get("ville"):
        parts.append(f"{profil.get('code_postal', '')} {profil.get('ville', '')}".strip())
    if parts:
        result["emetteur_adresse"] = "\n".join(parts)

    return result
