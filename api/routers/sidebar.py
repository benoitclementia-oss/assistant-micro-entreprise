"""Router sidebar — GET /sidebar (agrège profil + échéances + documents)."""

from agent import calendar_manager, documents, profile
from fastapi import APIRouter

from api.models import DocumentItem, EcheanceItem, ProfilResponse, SidebarData

router = APIRouter(prefix="/sidebar", tags=["sidebar"])


@router.get("", response_model=SidebarData)
def get_sidebar() -> SidebarData:
    """Agrège profil, échéances 30j et 5 derniers documents."""
    # Profil
    p = profile.consulter_profil()
    profil = ProfilResponse(
        nom=p.get("nom") or "",
        prenom=p.get("prenom") or "",
        nom_entreprise=p.get("nom_entreprise") or "",
        siret=p.get("siret") or "",
        adresse=p.get("adresse") or "",
        code_postal=p.get("code_postal") or "",
        ville=p.get("ville") or "",
        email=p.get("email") or "",
        telephone=p.get("telephone") or "",
        activite=p.get("activite") or "",
        regime_fiscal=p.get("regime_fiscal") or "",
        regime_social=p.get("regime_social") or "",
        date_creation_entreprise=p.get("date_creation_entreprise") or "",
    )

    # Échéances 30 prochains jours
    rows = calendar_manager.lister_echeances(30)
    echeances = [
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

    # 5 derniers documents
    docs_raw = documents.lister_documents()
    docs = [DocumentItem(**d) for d in docs_raw[-5:]]

    return SidebarData(profil=profil, echeances=echeances, documents=docs)
