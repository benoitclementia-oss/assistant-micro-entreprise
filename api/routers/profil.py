"""Router profil — GET /profil et PATCH /profil."""

from agent import profile
from fastapi import APIRouter

from api.models import ProfilResponse, ProfilUpdateRequest

router = APIRouter(prefix="/profil", tags=["profil"])


@router.get("", response_model=ProfilResponse)
def get_profil() -> ProfilResponse:
    """Retourne le profil utilisateur."""
    data = profile.consulter_profil()
    return ProfilResponse(
        nom=data.get("nom") or "",
        prenom=data.get("prenom") or "",
        nom_entreprise=data.get("nom_entreprise") or "",
        siret=data.get("siret") or "",
        adresse=data.get("adresse") or "",
        code_postal=data.get("code_postal") or "",
        ville=data.get("ville") or "",
        email=data.get("email") or "",
        telephone=data.get("telephone") or "",
        activite=data.get("activite") or "",
        regime_fiscal=data.get("regime_fiscal") or "",
        regime_social=data.get("regime_social") or "",
        date_creation_entreprise=data.get("date_creation_entreprise") or "",
    )


@router.patch("", response_model=ProfilResponse)
def update_profil(req: ProfilUpdateRequest) -> ProfilResponse:
    """Met à jour les champs non-nuls du profil."""
    champs = {k: v for k, v in req.model_dump().items() if v is not None}
    data = profile.modifier_profil(champs)
    return ProfilResponse(
        nom=data.get("nom") or "",
        prenom=data.get("prenom") or "",
        nom_entreprise=data.get("nom_entreprise") or "",
        siret=data.get("siret") or "",
        adresse=data.get("adresse") or "",
        code_postal=data.get("code_postal") or "",
        ville=data.get("ville") or "",
        email=data.get("email") or "",
        telephone=data.get("telephone") or "",
        activite=data.get("activite") or "",
        regime_fiscal=data.get("regime_fiscal") or "",
        regime_social=data.get("regime_social") or "",
        date_creation_entreprise=data.get("date_creation_entreprise") or "",
    )
