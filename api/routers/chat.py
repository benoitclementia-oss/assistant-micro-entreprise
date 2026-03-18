"""Router chat — POST /chat et POST /chat/clear."""

import asyncio
import logging

from agent.llm import Agent
from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_agent
from api.models import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, agent: Agent = Depends(get_agent)) -> ChatResponse:
    """Envoie un message a l'agent et retourne la reponse."""
    try:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, agent.chat, req.message)
        return ChatResponse(response=response)
    except TimeoutError:
        logger.error("Timeout lors de l'appel a l'agent")
        raise HTTPException(
            status_code=504,
            detail="La reponse a pris trop de temps. Essayez de reformuler votre question.",
        )
    except ConnectionError as e:
        logger.error("Erreur de connexion : %s", e)
        raise HTTPException(
            status_code=503,
            detail="Un service externe est temporairement indisponible (base juridique ou IA). Reessayez dans quelques instants.",
        )
    except Exception:
        logger.exception("Erreur inattendue dans le chat")
        raise HTTPException(
            status_code=500,
            detail="Une erreur inattendue s'est produite. Reessayez ou reformulez votre question.",
        )


@router.post("/clear")
async def clear_history(agent: Agent = Depends(get_agent)) -> dict:
    """Reinitialise l'historique de conversation."""
    agent.clear_history()
    return {"status": "ok"}
