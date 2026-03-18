"""Application FastAPI Assistant Micro-Entreprise."""

import logging
import os
from contextlib import asynccontextmanager

from agent.llm import Agent
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from qdrant_client import QdrantClient
from scripts import config

from api import deps

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Demarre et arrete le singleton Agent."""
    logger.info("Demarrage de l'agent Assistant Micro-Entreprise...")
    agent = Agent()
    deps.set_agent(agent)
    logger.info("Agent pret.")
    yield
    logger.info("Fermeture de la session agent...")
    agent.close_session()
    deps.set_agent(None)


app = FastAPI(title="Assistant Micro-Entreprise API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Middleware d'authentification ---

# Routes qui ne necessitent pas d'authentification
_PUBLIC_PATHS = {"/health", "/auth/login", "/auth/logout", "/auth/check"}


@app.middleware("http")
async def auth_middleware(request: Request, call_next) -> Response:
    """Verifie l'authentification pour toutes les routes protegees."""
    path = request.url.path

    # Routes publiques : pas de verification
    if path in _PUBLIC_PATHS:
        return await call_next(request)

    # Si APP_PASSWORD n'est pas defini, pas d'auth requise (mode dev)
    if not os.getenv("APP_PASSWORD"):
        return await call_next(request)

    # Verifier le cookie de session
    from api.routers.auth import verify_session

    if not verify_session(request):
        return Response(
            content='{"detail":"Non authentifie"}',
            status_code=401,
            media_type="application/json",
        )

    return await call_next(request)


from api.routers import auth, chat, documents, echeances, profil, sidebar  # noqa: E402

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(profil.router)
app.include_router(documents.router)
app.include_router(echeances.router)
app.include_router(sidebar.router)


@app.get("/health")
def health() -> dict:
    """Health check etendu : verifie Qdrant et la connectivite OpenAI."""
    status = {
        "status": "ok",
        "agent": deps._agent is not None,
        "qdrant": False,
        "openai_configured": bool(config.OPENAI_API_KEY),
    }

    # Verifier Qdrant
    try:
        client = QdrantClient(url=config.QDRANT_URL, timeout=5)
        client.get_collections()
        status["qdrant"] = True
    except Exception as e:
        status["qdrant"] = False
        status["qdrant_error"] = str(e)

    # Status global
    if not status["qdrant"] or not status["agent"]:
        status["status"] = "degraded"

    return status
