"""Dépendances FastAPI partagées (évite les imports circulaires)."""

from agent.llm import Agent

_agent: Agent | None = None


def get_agent() -> Agent:
    """Dependency injection : retourne le singleton Agent."""
    if _agent is None:
        raise RuntimeError("Agent non initialisé")
    return _agent


def set_agent(agent: Agent | None) -> None:
    """Initialise ou réinitialise le singleton Agent."""
    global _agent
    _agent = agent
