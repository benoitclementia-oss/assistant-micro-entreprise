"""Génération de documents avec brouillon et confirmation."""

import logging
import uuid
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Undefined

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_TEMPLATES_DIR = _PROJECT_ROOT / "templates"
_OUTPUT_DIR = _PROJECT_ROOT / "data" / "documents"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    keep_trailing_newline=True,
    undefined=Undefined,
)

VALID_TYPES = {"facture", "devis", "confirmation", "administratif"}

# Brouillons en mémoire (clé = draft_id)
_drafts: dict[str, dict] = {}


def preparer_document(type_doc: str, donnees: dict) -> dict:
    """Prépare un brouillon sans le sauvegarder.

    Retourne {"draft_id": str, "contenu": str, "type": str, "donnees": dict}.
    """
    if type_doc not in VALID_TYPES:
        raise ValueError(
            f"Type de document invalide : {type_doc}. "
            f"Types valides : {', '.join(sorted(VALID_TYPES))}"
        )

    if "date" not in donnees:
        donnees["date"] = datetime.now().strftime("%d/%m/%Y")

    if type_doc in ("facture", "devis") and "prestations" in donnees:
        donnees["total"] = sum(
            p.get("quantite", 1) * p.get("prix_unitaire", 0) for p in donnees["prestations"]
        )

    template = _env.get_template(f"{type_doc}.md")
    contenu = template.render(**donnees)

    draft_id = uuid.uuid4().hex[:8]
    _drafts[draft_id] = {
        "type": type_doc,
        "donnees": donnees,
        "contenu": contenu,
        "created_at": datetime.now().isoformat(),
    }

    logger.info("Brouillon préparé : %s (%s)", draft_id, type_doc)
    return {"draft_id": draft_id, "contenu": contenu, "type": type_doc}


def confirmer_document(draft_id: str) -> str:
    """Confirme et sauvegarde un brouillon. Retourne le chemin du fichier."""
    if draft_id not in _drafts:
        raise ValueError(
            f"Brouillon introuvable : {draft_id}. Utilisez preparer_document() d'abord."
        )

    draft = _drafts.pop(draft_id)
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    type_doc = draft["type"]
    donnees = draft["donnees"]
    contenu = draft["contenu"]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    numero = donnees.get("numero", donnees.get("reference", timestamp))
    filename = f"{type_doc}_{numero}.md"
    filepath = _OUTPUT_DIR / filename

    filepath.write_text(contenu, encoding="utf-8")
    logger.info("Document confirmé et sauvegardé : %s", filepath)

    return str(filepath)


def lister_documents() -> list[dict]:
    """Liste les documents déjà générés dans data/documents/."""
    if not _OUTPUT_DIR.exists():
        return []

    docs = []
    for f in sorted(_OUTPUT_DIR.glob("*.md")):
        stat = f.stat()
        docs.append(
            {
                "fichier": f.name,
                "taille": stat.st_size,
                "date": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
            }
        )
    return docs
