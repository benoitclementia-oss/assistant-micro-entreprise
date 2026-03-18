"""Router documents — GET /documents et GET /documents/{filename}."""

from pathlib import Path

from agent import documents
from fastapi import APIRouter, HTTPException

from api.models import DocumentItem

router = APIRouter(prefix="/documents", tags=["documents"])

_OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "documents"


@router.get("", response_model=list[DocumentItem])
def list_documents() -> list[DocumentItem]:
    """Liste les documents générés."""
    docs = documents.lister_documents()
    return [DocumentItem(**d) for d in docs]


@router.get("/{filename}")
def get_document(filename: str) -> dict:
    """Retourne le contenu d'un document Markdown."""
    # Sécurité : on ne veut pas de traversal de chemin
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Nom de fichier invalide")

    filepath = _OUTPUT_DIR / filename
    if not filepath.exists() or filepath.suffix != ".md":
        raise HTTPException(status_code=404, detail="Document introuvable")

    content = filepath.read_text(encoding="utf-8")
    return {"fichier": filename, "contenu": content}
