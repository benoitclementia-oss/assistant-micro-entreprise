"""Interface CLI interactive pour l'agent Assistant Micro-Entreprise."""

import logging
import sys

from .llm import Agent

# Codes ANSI
BOLD = "\033[1m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
DIM = "\033[2m"
RESET = "\033[0m"

HELP_TEXT = f"""\
{BOLD}Commandes disponibles :{RESET}
  {CYAN}help{RESET}    — Afficher cette aide
  {CYAN}clear{RESET}   — Réinitialiser la conversation
  {CYAN}profil{RESET}  — Afficher le profil utilisateur
  {CYAN}quit{RESET}    — Quitter l'application (sauvegarde la session)
"""

WELCOME = f"""\
{BOLD}{CYAN}╔══════════════════════════════════════════════════════════════╗
║                    Assistant Micro-Entreprise v0.2                                     ║
║   Assistant juridique et administratif — micro-entreprises   ║
╚══════════════════════════════════════════════════════════════╝{RESET}

Posez vos questions sur la fiscalité, la comptabilité ou les obligations
des micro-entreprises. Tapez {CYAN}help{RESET} pour l'aide, {CYAN}quit{RESET} pour quitter.
"""


def main() -> None:
    """Boucle principale du CLI interactif."""
    # Forcer UTF-8 sur Windows pour supporter les caracteres speciaux
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr.encoding != "utf-8":
        sys.stderr.reconfigure(encoding="utf-8")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    # Réduire le bruit des libs externes
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    agent = Agent()
    print(WELCOME)

    try:
        while True:
            try:
                user_input = input(f"{BOLD}Vous :{RESET} ").strip()
            except (EOFError, KeyboardInterrupt):
                print(f"\n{DIM}Sauvegarde de la session...{RESET}")
                agent.close_session()
                print(f"{DIM}Au revoir !{RESET}")
                break

            if not user_input:
                continue

            cmd = user_input.lower()
            if cmd in ("quit", "exit", "q"):
                print(f"{DIM}Sauvegarde de la session...{RESET}")
                agent.close_session()
                print(f"{DIM}Au revoir !{RESET}")
                break
            elif cmd == "help":
                print(HELP_TEXT)
                continue
            elif cmd == "clear":
                agent.clear_history()
                print(f"{DIM}Conversation réinitialisée.{RESET}")
                continue
            elif cmd == "profil":
                from . import profile

                profil = profile.consulter_profil()
                remplis = {k: v for k, v in profil.items() if k in profile.CHAMPS_PROFIL and v}
                if remplis:
                    print(f"\n{BOLD}Profil utilisateur :{RESET}")
                    for k, v in remplis.items():
                        print(f"  {CYAN}{k}{RESET}: {v}")
                else:
                    print(f"{DIM}Profil vide. Complétez votre profil via le chat.{RESET}")
                print()
                continue

            print(f"{DIM}Recherche en cours...{RESET}")
            try:
                response = agent.chat(user_input)
                print(f"\n{BOLD}{YELLOW}Assistant :{RESET} {response}\n")
            except Exception as e:
                logging.getLogger(__name__).exception("Erreur agent")
                print(f"\n{BOLD}Erreur :{RESET} {e}\n")
    except Exception:
        # Sauvegarder la session même en cas d'erreur inattendue
        agent.close_session()
        raise
