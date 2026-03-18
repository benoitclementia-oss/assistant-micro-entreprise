"""Client pour l'API Legifrance (PISTE) — environnement sandbox."""

import logging
import time
from datetime import date
from typing import Any

import requests

from . import config

logger = logging.getLogger(__name__)

OAUTH_URL = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
API_BASE = "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app"

# Rate limiting
REQUEST_DELAY = 0.5  # secondes entre chaque requete
MAX_RETRIES = 5
BACKOFF_FACTOR = 2

# Renouvellement proactif du token toutes les 58 minutes
TOKEN_REFRESH_INTERVAL = 58 * 60  # secondes
MIN_AUTH_COOLDOWN = 10  # secondes minimum entre deux tentatives d'auth


class LegifranceClient:
    def __init__(self) -> None:
        self._session = requests.Session()
        self._token: str | None = None
        self._token_expires_at: float = 0
        self._token_obtained_at: float = 0
        self._last_auth_attempt: float = 0
        self._last_request_time: float = 0

    # ------------------------------------------------------------------
    # Authentification OAuth2
    # ------------------------------------------------------------------
    def _authenticate(self) -> None:
        # Cooldown : empecher les tentatives d'auth trop rapprochees
        since_last = time.time() - self._last_auth_attempt
        if self._last_auth_attempt > 0 and since_last < MIN_AUTH_COOLDOWN:
            wait = MIN_AUTH_COOLDOWN - since_last
            logger.info("Auth cooldown : attente %.1f s...", wait)
            time.sleep(wait)

        self._last_auth_attempt = time.time()
        logger.info("Authentification OAuth2 aupres de PISTE...")
        resp = requests.post(
            OAUTH_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": config.LEGIFRANCE_CLIENT_ID,
                "client_secret": config.LEGIFRANCE_CLIENT_SECRET,
                "scope": "openid",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        now = time.time()
        self._token_obtained_at = now
        self._token_expires_at = now + TOKEN_REFRESH_INTERVAL
        logger.info("Token OAuth2 obtenu (prochain renouvellement dans 58 min).")

    def _ensure_token(self) -> None:
        if self._token is None or time.time() >= self._token_expires_at:
            self._authenticate()

    # ------------------------------------------------------------------
    # Requete generique avec rate-limiting et retry
    # ------------------------------------------------------------------
    def _request(self, method: str, path: str, **kwargs: Any) -> dict:
        self._ensure_token()

        elapsed = time.time() - self._last_request_time
        if elapsed < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed)

        url = f"{API_BASE}{path}"
        headers = {"Authorization": f"Bearer {self._token}"}

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = self._session.request(method, url, headers=headers, **kwargs)
                self._last_request_time = time.time()

                if resp.status_code == 401:
                    logger.warning("Token expire, renouvellement...")
                    self._authenticate()
                    headers["Authorization"] = f"Bearer {self._token}"
                    continue

                if resp.status_code == 429:
                    wait = BACKOFF_FACTOR**attempt
                    logger.warning("Rate limited, attente %s s...", wait)
                    time.sleep(wait)
                    continue

                resp.raise_for_status()
                return resp.json()

            except requests.exceptions.HTTPError as exc:
                # 400 Bad Request = erreur permanente, ne pas retrier
                if exc.response is not None and exc.response.status_code == 400:
                    raise
                if attempt == MAX_RETRIES:
                    raise
                wait = BACKOFF_FACTOR**attempt
                logger.warning(
                    "Erreur requete (tentative %d/%d) : %s — retry dans %s s",
                    attempt,
                    MAX_RETRIES,
                    exc,
                    wait,
                )
                time.sleep(wait)
            except requests.exceptions.RequestException as exc:
                if attempt == MAX_RETRIES:
                    raise
                wait = BACKOFF_FACTOR**attempt
                logger.warning(
                    "Erreur requete (tentative %d/%d) : %s — retry dans %s s",
                    attempt,
                    MAX_RETRIES,
                    exc,
                    wait,
                )
                time.sleep(wait)

        raise RuntimeError(f"Echec apres {MAX_RETRIES} tentatives : {url}")

    # ------------------------------------------------------------------
    # Endpoints bas niveau
    # ------------------------------------------------------------------
    def get_table_matieres(self, text_id: str) -> dict:
        """Recuperer la table des matieres d'un code (date = aujourd'hui)."""
        return self._request(
            "POST",
            "/consult/code/tableMatieres",
            json={"textId": text_id, "date": str(date.today())},
        )

    def get_table_matieres_legi(self, text_id: str) -> dict:
        """Recuperer la TDM d'un texte legislatif (LODA : lois, decrets, arretes)."""
        return self._request(
            "POST",
            "/consult/legi/tableMatieres",
            json={"textId": text_id, "date": str(date.today())},
        )

    def get_article(self, article_id: str) -> dict:
        """Recuperer le contenu complet d'un article par son ID LEGIARTI."""
        return self._request(
            "POST",
            "/consult/getArticle",
            json={"id": article_id},
        )

    def search(
        self,
        query: str,
        fonds: str = "LODA_ETAT",
        page_number: int = 1,
        page_size: int = 100,
    ) -> dict:
        """Recherche full-text dans un fond (CODE_ETAT, LODA_ETAT, etc.)."""
        return self._request(
            "POST",
            "/search",
            json={
                "fond": fonds,
                "recherche": {
                    "champs": [
                        {
                            "typeChamp": "ALL",
                            "criteres": [
                                {
                                    "typeRecherche": "EXACTE",
                                    "valeur": query,
                                    "operateur": "ET",
                                }
                            ],
                            "operateur": "ET",
                        }
                    ],
                    "filtres": [],
                    "pageNumber": page_number,
                    "pageSize": page_size,
                    "sort": "PERTINENCE",
                    "typePagination": "DEFAUT",
                },
            },
        )

    # ------------------------------------------------------------------
    # Methodes de haut niveau
    # ------------------------------------------------------------------
    def fetch_articles_from_code(self, text_id: str, code_nom: str) -> list[dict]:
        """Parcourir la TDM d'un code, puis recuperer chaque article."""
        logger.info("Recuperation de la table des matieres : %s", code_nom)
        toc = self.get_table_matieres(text_id)

        # Extraire tous les stubs d'articles (id, etat, num) depuis la TDM
        stubs = self._collect_article_stubs(toc)
        # Filtrer : uniquement VIGUEUR
        stubs = [s for s in stubs if s["etat"] == "VIGUEUR"]
        logger.info("  %d articles en vigueur dans la TDM de %s", len(stubs), code_nom)

        articles: list[dict] = []
        for i, stub in enumerate(stubs, 1):
            if i % 50 == 0 or i == 1:
                logger.info("  Recuperation article %d/%d...", i, len(stubs))
            try:
                data = self.get_article(stub["article_id"])
                art_data = data.get("article", {})
                if not art_data:
                    continue
                articles.append(
                    {
                        "article_id": stub["article_id"],
                        "titre": art_data.get("num", stub.get("num", "")),
                        "texte": art_data.get("texte", ""),
                        "texte_html": art_data.get("texteHtml", ""),
                        "code_source": code_nom,
                        "date_publication": art_data.get("dateDebut", ""),
                        "etat": art_data.get("etat", stub["etat"]),
                    }
                )
            except Exception:
                logger.warning(
                    "  Erreur sur l'article %s, on continue...",
                    stub["article_id"],
                    exc_info=True,
                )

        logger.info("  %d articles recuperes depuis %s", len(articles), code_nom)
        return articles

    def fetch_articles_from_search(
        self,
        query: str,
        fonds: str = "LODA_ETAT",
        skip_text_ids: set[str] | None = None,
    ) -> list[dict]:
        """Rechercher des textes, puis recuperer les articles complets.

        Args:
            skip_text_ids: IDs de textes deja recuperes (pour resume).
        """
        logger.info("Recherche '%s' dans le fond %s", query, fonds)
        text_ids: list[dict] = []
        page = 1

        while True:
            data = self.search(query, fonds=fonds, page_number=page)
            results = data.get("results", [])
            if not results:
                break

            for result in results:
                titles = result.get("titles", [])
                for title_info in titles:
                    tid = title_info.get("id", "")
                    status = title_info.get("legalStatus", "")
                    title = title_info.get("title", "")
                    if tid and status == "VIGUEUR":
                        text_ids.append(
                            {
                                "text_id": tid.split("_")[0] if "_" in tid else tid,
                                "title": title,
                            }
                        )

            total_count = data.get("totalResultNumber", 0)
            if page * 100 >= total_count:
                break
            page += 1

        logger.info(
            "  %d textes en vigueur trouves, recuperation des articles...",
            len(text_ids),
        )

        # Pour chaque texte trouve, recuperer sa TDM et ses articles
        articles: list[dict] = []
        seen_texts: set[str] = set(skip_text_ids or set())
        skipped = len(seen_texts)
        all_unique = {i["text_id"] for i in text_ids}
        total_unique = len(all_unique)
        if skipped:
            to_skip = seen_texts & all_unique
            logger.info("  %d/%d textes deja en cache, skip", len(to_skip), total_unique)
        text_count = 0
        article_count = 0
        for info in text_ids:
            tid = info["text_id"]
            if tid in seen_texts:
                continue
            seen_texts.add(tid)
            text_count += 1
            logger.info(
                "  Texte %d/%d : %s (%s)",
                text_count,
                total_unique,
                info["title"][:60],
                tid,
            )
            try:
                toc = self.get_table_matieres_legi(tid)
                stubs = self._collect_article_stubs(toc)
                stubs = [s for s in stubs if s["etat"] == "VIGUEUR"]
                logger.info("    %d articles en vigueur", len(stubs))
                for i_stub, stub in enumerate(stubs, 1):
                    article_count += 1
                    if i_stub % 50 == 0 or i_stub == 1:
                        logger.info("    Recuperation article %d/%d...", i_stub, len(stubs))

                    try:
                        data = self.get_article(stub["article_id"])
                        art_data = data.get("article", {})
                        if not art_data:
                            continue
                        articles.append(
                            {
                                "article_id": stub["article_id"],
                                "titre": art_data.get("num", ""),
                                "texte": art_data.get("texte", ""),
                                "texte_html": art_data.get("texteHtml", ""),
                                "code_source": f"Recherche: {query} — {info['title']}",
                                "date_publication": art_data.get("dateDebut", ""),
                                "etat": art_data.get("etat", "VIGUEUR"),
                            }
                        )
                    except Exception:
                        logger.warning(
                            "  Erreur article %s, on continue...",
                            stub["article_id"],
                            exc_info=True,
                        )
            except Exception:
                logger.warning(
                    "  Erreur TDM pour texte %s, on continue...",
                    tid,
                    exc_info=True,
                )

        logger.info("  %d articles recuperes via recherche '%s'", len(articles), query)
        return articles

    # ------------------------------------------------------------------
    # Utilitaires internes
    # ------------------------------------------------------------------
    def _collect_article_stubs(self, node: Any) -> list[dict]:
        """Extraire recursivement tous les stubs d'articles depuis la TDM."""
        stubs: list[dict] = []

        def _walk(n: Any) -> None:
            if not isinstance(n, dict):
                return
            # Les articles dans la TDM ont un id LEGIARTI
            for art in n.get("articles", []):
                art_id = art.get("id", "")
                if art_id.startswith("LEGIARTI"):
                    stubs.append(
                        {
                            "article_id": art_id,
                            "num": art.get("num", ""),
                            "etat": art.get("etat", "VIGUEUR"),
                        }
                    )
            for section in n.get("sections", []):
                _walk(section)

        _walk(node)
        return stubs
