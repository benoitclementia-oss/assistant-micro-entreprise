"""Router authentification — POST /auth/login et POST /auth/logout."""

import hmac
import os
import secrets

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

# Token de session généré au démarrage (en mémoire uniquement)
_SESSION_SECRET = secrets.token_hex(32)
_active_tokens: set[str] = set()


def _get_app_password() -> str:
    """Récupère le mot de passe défini dans .env (APP_PASSWORD)."""
    pwd = os.getenv("APP_PASSWORD", "")
    if not pwd:
        raise RuntimeError(
            "APP_PASSWORD non défini dans .env — "
            "l'authentification est impossible sans mot de passe."
        )
    return pwd


def _generate_token() -> str:
    """Génère un token de session unique."""
    token = secrets.token_hex(32)
    _active_tokens.add(token)
    return token


def verify_session(request: Request) -> bool:
    """Vérifie si la requête contient un token de session valide."""
    token = request.cookies.get("jd_session")
    if not token:
        return False
    return token in _active_tokens


class LoginRequest(BaseModel):
    password: str


@router.post("/login")
async def login(req: LoginRequest, response: Response) -> dict:
    """Vérifie le mot de passe et crée une session."""
    app_password = _get_app_password()

    if not hmac.compare_digest(req.password, app_password):
        return {"status": "error", "message": "Mot de passe incorrect"}

    token = _generate_token()
    response.set_cookie(
        key="jd_session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400 * 7,  # 7 jours
    )
    return {"status": "ok"}


@router.post("/logout")
async def logout(response: Response, request: Request) -> dict:
    """Supprime la session."""
    token = request.cookies.get("jd_session")
    if token:
        _active_tokens.discard(token)
    response.delete_cookie("jd_session")
    return {"status": "ok"}


@router.get("/check")
async def check_auth(request: Request) -> dict:
    """Vérifie si l'utilisateur est authentifié."""
    return {"authenticated": verify_session(request)}
