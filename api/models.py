"""Modèles Pydantic pour l'API Assistant Micro-Entreprise."""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


class ProfilUpdateRequest(BaseModel):
    nom: str | None = None
    prenom: str | None = None
    nom_entreprise: str | None = None
    siret: str | None = None
    adresse: str | None = None
    code_postal: str | None = None
    ville: str | None = None
    email: str | None = None
    telephone: str | None = None
    activite: str | None = None
    regime_fiscal: str | None = None
    regime_social: str | None = None
    date_creation_entreprise: str | None = None


class ProfilResponse(BaseModel):
    nom: str = ""
    prenom: str = ""
    nom_entreprise: str = ""
    siret: str = ""
    adresse: str = ""
    code_postal: str = ""
    ville: str = ""
    email: str = ""
    telephone: str = ""
    activite: str = ""
    regime_fiscal: str = ""
    regime_social: str = ""
    date_creation_entreprise: str = ""


class EcheanceItem(BaseModel):
    id: int
    titre: str
    date: str
    description: str = ""
    type: str = "custom"
    fait: bool = False


class EcheanceCreateRequest(BaseModel):
    titre: str
    date: str
    description: str = ""
    type_echeance: str = "custom"


class DocumentItem(BaseModel):
    fichier: str
    taille: int
    date: str


class SidebarData(BaseModel):
    profil: ProfilResponse
    echeances: list[EcheanceItem]
    documents: list[DocumentItem]
