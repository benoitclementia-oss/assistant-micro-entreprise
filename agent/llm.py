"""Agent GPT-4o avec function calling pour Assistant Micro-Entreprise."""

import json
import logging

from openai import APIConnectionError, APITimeoutError, OpenAI
from scripts import config

from . import calendar_manager, documents, email_sender, memory, profile, rag
from .tools import TOOLS

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT_BASE = """\
Tu es un assistant juridique et administratif spécialisé pour les \
micro-entreprises françaises (auto-entrepreneurs).

Ton rôle :
- Répondre aux questions sur la fiscalité, la comptabilité et les obligations \
administratives des micro-entreprises en te basant sur les textes de loi français.
- Préparer des documents administratifs et commerciaux (factures, devis, etc.).
- Gérer le calendrier des échéances fiscales et sociales.
- Envoyer des emails professionnels.
- Mémoriser les informations importantes pour les sessions futures.

Règles :
- Utilise TOUJOURS l'outil recherche_juridique pour chercher dans la base de \
textes juridiques avant de répondre à une question de droit. Ne réponds jamais \
de mémoire sur un sujet juridique sans vérifier.
- Cite les articles de loi pertinents dans tes réponses (ex: "Article 293 B du CGI").
- Réponds en français, de manière claire et accessible.
- Si tu n'es pas sûr d'une information juridique, dis-le explicitement.
- Pour les documents, utilise TOUJOURS preparer_document() d'abord pour montrer \
un brouillon, puis confirmer_document() après validation de l'utilisateur. \
Ne sauvegarde JAMAIS un document sans confirmation explicite.
- Pour les emails, demande confirmation avant d'envoyer.
- Quand l'utilisateur donne des informations personnelles ou d'entreprise \
(nom, prénom, SIRET, adresse, activité, régime fiscal, etc.), utilise \
TOUJOURS modifier_profil() pour les enregistrer dans le profil. \
Ne les mets PAS dans memoriser() — le profil est fait pour ça.
- Utilise memoriser() uniquement pour les informations métier, préférences, \
clients, décisions, et autres données qui ne sont pas des champs de profil.
- Utilise le profil utilisateur pour pré-remplir les champs émetteur des documents.

IMPORTANT — Périmètre strict :
Tu ne traites QUE les sujets liés aux micro-entreprises françaises :
fiscalité, comptabilité, obligations administratives, droit de la consommation, \
protection sociale, RGPD, documents commerciaux (factures, devis), échéances, \
et les démarches d'un auto-entrepreneur.

Si l'utilisateur pose une question hors de ce périmètre (culture générale, \
médecine, cuisine, sport, programmation, politique, etc.), refuse poliment \
en expliquant que tu es spécialisé dans l'accompagnement des micro-entreprises \
et propose de reformuler la question dans ce cadre.
Ne donne JAMAIS de réponse sur un sujet hors périmètre, même si tu connais \
la réponse. C'est une question de crédibilité et de responsabilité.
"""

MAX_HISTORY = 50
KEEP_RECENT = 20
MAX_TOOL_ROUNDS = 10


class Agent:
    """Agent conversationnel avec function calling GPT-4o."""

    def __init__(self) -> None:
        self._client = OpenAI(api_key=config.OPENAI_API_KEY, timeout=30.0)
        self._session_id = memory.start_session()
        system_prompt = self._build_system_prompt()
        self._history: list[dict] = [
            {"role": "system", "content": system_prompt},
        ]

    def chat(self, user_message: str) -> str:
        """Envoie un message et retourne la réponse de l'agent."""
        self._history.append({"role": "user", "content": user_message})
        self._trim_history()

        try:
            response = self._client.chat.completions.create(
                model="gpt-4o",
                messages=self._history,
                tools=TOOLS,
            )
        except APITimeoutError as err:
            logger.error("Timeout OpenAI lors de la requete initiale")
            raise TimeoutError("OpenAI n'a pas repondu dans le delai imparti.") from err
        except APIConnectionError as e:
            logger.error("Connexion OpenAI echouee : %s", e)
            raise ConnectionError("Impossible de contacter le service IA.") from e

        message = response.choices[0].message

        # Boucle de function calling (avec limite de securite)
        tool_rounds = 0
        while message.tool_calls and tool_rounds < MAX_TOOL_ROUNDS:
            tool_rounds += 1
            self._history.append(message.model_dump())

            for tool_call in message.tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                logger.info("Tool call [%d/%d]: %s(%s)", tool_rounds, MAX_TOOL_ROUNDS, name, args)

                result = self._execute_tool(name, args)

                self._history.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )

            try:
                response = self._client.chat.completions.create(
                    model="gpt-4o",
                    messages=self._history,
                    tools=TOOLS,
                )
            except APITimeoutError as err:
                logger.error("Timeout OpenAI lors du round %d", tool_rounds)
                raise TimeoutError("OpenAI n'a pas repondu dans le delai imparti.") from err
            except APIConnectionError as e:
                logger.error("Connexion OpenAI echouee au round %d : %s", tool_rounds, e)
                raise ConnectionError("Impossible de contacter le service IA.") from e
            message = response.choices[0].message

        assistant_content = message.content or ""
        self._history.append({"role": "assistant", "content": assistant_content})
        return assistant_content

    def clear_history(self) -> None:
        """Réinitialise l'historique de conversation."""
        system_prompt = self._build_system_prompt()
        self._history = [
            {"role": "system", "content": system_prompt},
        ]

    def close_session(self) -> None:
        """Ferme la session : génère un résumé et le sauvegarde."""
        try:
            memory.close_session(self._session_id, self._history, client=self._client)
            logger.info("Session %d fermée", self._session_id)
        except Exception:
            logger.exception("Erreur lors de la fermeture de session")

    def _build_system_prompt(self) -> str:
        """Construit le system prompt dynamique avec profil, mémoire, sessions."""
        parts = [_SYSTEM_PROMPT_BASE]

        # Profil utilisateur
        profil_text = profile.profil_pour_prompt()
        if profil_text:
            parts.append(profil_text)

        # Faits mémorisés
        faits_text = memory.faits_pour_prompt()
        if faits_text:
            parts.append(faits_text)

        # Sessions précédentes
        sessions_text = memory.sessions_pour_prompt()
        if sessions_text:
            parts.append(sessions_text)

        # Note nouvel utilisateur
        if profile.profil_est_vide():
            parts.append(
                "## Note\n"
                "Le profil utilisateur est quasiment vide. "
                "Propose à l'utilisateur de le remplir en lui demandant "
                "ses informations (nom, entreprise, SIRET, adresse, activité, etc.). "
                "Cela permettra de pré-remplir automatiquement les documents."
            )

        return "\n\n".join(parts)

    def _trim_history(self) -> None:
        """Tronque l'historique si trop long (garde system + derniers messages).

        Ne coupe jamais au milieu d'une séquence tool_calls → tool results,
        sinon l'API OpenAI rejettera la requête.
        """
        if len(self._history) <= MAX_HISTORY:
            return
        system = self._history[0]
        cut = len(self._history) - KEEP_RECENT
        while cut > 1:
            msg = self._history[cut]
            role = msg.get("role", "")
            if role == "user" or (role == "assistant" and not msg.get("tool_calls")):
                break
            cut -= 1
        self._history = [system] + self._history[cut:]

    def _execute_tool(self, name: str, args: dict) -> str:
        """Dispatch l'appel d'outil vers le bon module."""
        try:
            match name:
                case "recherche_juridique":
                    return self._tool_recherche(**args)
                case "preparer_document":
                    return self._tool_preparer_document(**args)
                case "confirmer_document":
                    return self._tool_confirmer_document(**args)
                case "lister_documents":
                    return self._tool_lister_documents()
                case "lister_echeances":
                    return self._tool_lister_echeances(**args)
                case "ajouter_echeance":
                    return self._tool_ajouter_echeance(**args)
                case "envoyer_email":
                    return self._tool_envoyer_email(**args)
                case "memoriser":
                    return self._tool_memoriser(**args)
                case "rappeler":
                    return self._tool_rappeler(**args)
                case "consulter_profil":
                    return self._tool_consulter_profil()
                case "modifier_profil":
                    return self._tool_modifier_profil(**args)
                case _:
                    return f"Outil inconnu : {name}"
        except Exception as e:
            logger.exception("Erreur dans l'outil %s", name)
            return f"Erreur lors de l'exécution de {name} : {e}"

    # --- Tools : Recherche ---

    def _tool_recherche(self, query: str, collections: list[str] | None = None) -> str:
        results = rag.search(query, collections=collections)
        if not results:
            return "Aucun résultat trouvé dans la base juridique."
        context = rag.format_context(results)
        return f"Résultats de la recherche ({len(results)} articles) :\n\n{context}"

    # --- Tools : Documents ---

    def _tool_preparer_document(self, type: str, donnees: dict | None = None, **kwargs) -> str:
        # GPT-4o peut envoyer les données dans 'donnees' ou directement comme kwargs
        if donnees is None:
            donnees = kwargs
        # Auto-injection des données émetteur depuis le profil
        emetteur = profile.donnees_emetteur()
        for k, v in emetteur.items():
            if k not in donnees:
                donnees[k] = v

        result = documents.preparer_document(type, donnees)
        return (
            f"Brouillon préparé (draft_id: {result['draft_id']})\n\n"
            f"--- APERÇU DU DOCUMENT ---\n\n{result['contenu']}\n\n"
            f"--- FIN DE L'APERÇU ---\n\n"
            "Montre ce brouillon à l'utilisateur et demande confirmation "
            "avant d'appeler confirmer_document()."
        )

    def _tool_confirmer_document(self, draft_id: str) -> str:
        path = documents.confirmer_document(draft_id)
        return f"Document confirmé et sauvegardé : {path}"

    def _tool_lister_documents(self) -> str:
        docs = documents.lister_documents()
        if not docs:
            return "Aucun document généré pour le moment."
        lines = []
        for d in docs:
            lines.append(f"- {d['fichier']} ({d['taille']} octets, {d['date']})")
        return f"{len(docs)} document(s) :\n" + "\n".join(lines)

    # --- Tools : Calendrier ---

    def _tool_lister_echeances(self, jours: int = 30) -> str:
        echeances = calendar_manager.lister_echeances(jours)
        if not echeances:
            return f"Aucune échéance dans les {jours} prochains jours."
        lines = []
        for e in echeances:
            status = "[FAIT]" if e["fait"] else "[    ]"
            lines.append(
                f"{status} {e['date']} — {e['titre']}"
                + (f" ({e['type']})" if e["type"] != "custom" else "")
                + (f"\n         {e['description']}" if e["description"] else "")
            )
        return "\n".join(lines)

    def _tool_ajouter_echeance(
        self,
        titre: str,
        date: str,
        description: str = "",
        type_echeance: str = "custom",
    ) -> str:
        echeance_id = calendar_manager.ajouter_echeance(titre, date, description, type_echeance)
        return f"Échéance ajoutée (id={echeance_id}) : {titre} le {date}"

    # --- Tools : Email ---

    def _tool_envoyer_email(self, destinataire: str, objet: str, corps: str) -> str:
        ok = email_sender.envoyer_email(destinataire, objet, corps)
        if ok:
            return f"Email envoyé à {destinataire} avec l'objet « {objet} »."
        return "Échec de l'envoi de l'email. Vérifiez la configuration Gmail."

    # --- Tools : Mémoire ---

    def _tool_memoriser(self, categorie: str, cle: str, valeur: str) -> str:
        result = memory.memoriser(categorie, cle, valeur, source="conversation")
        return f"Mémorisé : [{result['categorie']}] {result['cle']} = {result['valeur']}"

    def _tool_rappeler(self, categorie: str | None = None, query: str = "") -> str:
        faits = memory.rappeler(categorie=categorie, query=query)
        if not faits:
            filtre = f" (catégorie: {categorie})" if categorie else ""
            return f"Aucun fait trouvé{filtre}."
        lines = []
        for f in faits:
            lines.append(f"[{f['categorie']}] {f['cle']} = {f['valeur']}")
        return f"{len(faits)} fait(s) trouvé(s) :\n" + "\n".join(lines)

    # --- Tools : Profil ---

    def _tool_consulter_profil(self) -> str:
        profil = profile.consulter_profil()
        remplis = {k: v for k, v in profil.items() if k in profile.CHAMPS_PROFIL and v}
        if not remplis:
            return "Le profil est vide. Utilisez modifier_profil() pour le remplir."
        lines = []
        for k, v in remplis.items():
            lines.append(f"- {k}: {v}")
        return "Profil utilisateur :\n" + "\n".join(lines)

    def _tool_modifier_profil(self, **kwargs: str) -> str:
        # Les champs arrivent directement comme kwargs
        champs = {k: v for k, v in kwargs.items() if k in profile.CHAMPS_PROFIL}
        profile.modifier_profil(champs)
        modifies = [k for k in champs if k in profile.CHAMPS_PROFIL]
        if not modifies:
            return "Aucun champ valide modifié. Champs possibles : " + ", ".join(
                profile.CHAMPS_PROFIL
            )
        return f"Profil mis à jour : {', '.join(modifies)}"
