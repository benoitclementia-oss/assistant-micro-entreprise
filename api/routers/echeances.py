"""Router échéances — GET/POST /echeances et PATCH /echeances/{id}/fait."""

from agent import calendar_manager
from fastapi import APIRouter, HTTPException

from api.models import EcheanceCreateRequest, EcheanceItem

router = APIRouter(prefix="/echeances", tags=["echeances"])


@router.get("", response_model=list[EcheanceItem])
def list_echeances(jours: int = 30) -> list[EcheanceItem]:
    """Liste les échéances des N prochains jours."""
    rows = calendar_manager.lister_echeances(jours)
    return [
        EcheanceItem(
            id=r["id"],
            titre=r["titre"],
            date=r["date"],
            description=r.get("description") or "",
            type=r.get("type") or "custom",
            fait=bool(r.get("fait", False)),
        )
        for r in rows
    ]


@router.post("", response_model=EcheanceItem)
def create_echeance(req: EcheanceCreateRequest) -> EcheanceItem:
    """Ajoute une nouvelle échéance."""
    echeance_id = calendar_manager.ajouter_echeance(
        req.titre, req.date, req.description, req.type_echeance
    )
    rows = calendar_manager.lister_echeances(jours=3650)
    row = next((r for r in rows if r["id"] == echeance_id), None)
    if row is None:
        raise HTTPException(status_code=500, detail="Échéance créée mais introuvable")
    return EcheanceItem(
        id=row["id"],
        titre=row["titre"],
        date=row["date"],
        description=row.get("description") or "",
        type=row.get("type") or "custom",
        fait=bool(row.get("fait", False)),
    )


@router.patch("/{echeance_id}/fait")
def mark_done(echeance_id: int) -> dict:
    """Marque une échéance comme faite."""
    calendar_manager.marquer_fait(echeance_id)
    return {"status": "ok", "id": echeance_id}
