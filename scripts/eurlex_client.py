"""Client EUR-Lex — téléchargement et parsing de règlements européens (version FR).

Les règlements sont accessibles publiquement sans authentification via l'URL :
  https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=CELEX:{celex}

Stratégie de parsing :
  1. Chercher les <div class="eli-subdivision" id="art_*"> (structure ELI moderne)
  2. Fallback : découper le texte brut par "Article N" (anciens documents)
"""

import logging
import re
import time

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_EURLEX_HTML_URL = "https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=CELEX:{celex}"
_REQUEST_DELAY = 2.0  # secondes — politesse vis-à-vis d'EUR-Lex


class EurlexClient:
    def __init__(self) -> None:
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (compatible; MicroEntreprise-LegalBot/1.0; "
                    "+https://github.com/research)"
                ),
                "Accept-Language": "fr-FR,fr;q=0.9",
            }
        )
        self._last_request_time: float = 0

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    def _get(self, url: str) -> str:
        """Télécharger une URL avec rate limiting."""
        elapsed = time.time() - self._last_request_time
        if elapsed < _REQUEST_DELAY:
            time.sleep(_REQUEST_DELAY - elapsed)
        resp = self._session.get(url, timeout=30)
        self._last_request_time = time.time()
        resp.raise_for_status()
        return resp.text

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def fetch_regulation(self, celex: str, nom: str) -> list[dict]:
        """Télécharger et parser un règlement EU depuis EUR-Lex.

        Returns:
            Liste d'articles au format unifié Assistant Micro-Entreprise :
            {article_id, titre, texte, texte_html, code_source,
             date_publication, etat, source, celex}
        """
        url = _EURLEX_HTML_URL.format(celex=celex)
        logger.info("EUR-Lex : téléchargement de %s (%s)", nom, celex)

        try:
            html = self._get(url)
        except requests.exceptions.HTTPError as exc:
            logger.error("Erreur HTTP EUR-Lex %s : %s", celex, exc)
            return []
        except requests.exceptions.RequestException as exc:
            logger.error("Erreur réseau EUR-Lex %s : %s", celex, exc)
            return []

        articles = self._parse_html(html, celex, nom)
        logger.info("  %d articles extraits depuis %s", len(articles), celex)
        return articles

    # ------------------------------------------------------------------
    # Parsing HTML
    # ------------------------------------------------------------------

    def _parse_html(self, html: str, celex: str, nom: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")

        # Supprimer les éléments non-contenu
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "figure"]):
            tag.decompose()

        # Stratégie 1 : structure ELI moderne (<div class="eli-subdivision">)
        articles = self._parse_eli(soup, celex, nom)
        if articles:
            return articles

        # Stratégie 2 : balises <article> ou <div id="art_N">
        articles = self._parse_article_tags(soup, celex, nom)
        if articles:
            return articles

        # Stratégie 3 : fallback texte brut — découpe par "Article N"
        full_text = soup.get_text(separator="\n", strip=True)
        return self._split_by_article_marker(full_text, celex, nom)

    def _parse_eli(self, soup: BeautifulSoup, celex: str, nom: str) -> list[dict]:
        """Stratégie ELI : <div class="eli-subdivision" id="art_*">."""
        results = []
        for div in soup.find_all("div", attrs={"id": re.compile(r"^art_")}):
            art_id_attr = div["id"]  # ex: "art_1"
            # Titre de l'article
            title_tag = div.find(class_=re.compile(r"oj-ti-art|eli-title|doc-ti-art", re.I))
            titre = (
                title_tag.get_text(strip=True)
                if title_tag
                else art_id_attr.replace("_", " ").title()
            )
            texte = div.get_text(separator=" ", strip=True)
            texte_html = str(div)
            if not texte:
                continue
            results.append(_make_article(art_id_attr, titre, texte, texte_html, celex, nom))
        return results

    def _parse_article_tags(self, soup: BeautifulSoup, celex: str, nom: str) -> list[dict]:
        """Stratégie balises <article> ou <div id='article-N'>."""
        results = []
        candidates = soup.find_all(
            ["article"],
        ) or soup.find_all("div", attrs={"id": re.compile(r"article[-_]\d+", re.I)})
        for elem in candidates:
            art_id_attr = elem.get("id", f"art_{len(results) + 1}")
            h_tag = elem.find(re.compile(r"h[1-6]"))
            titre = h_tag.get_text(strip=True) if h_tag else art_id_attr
            texte = elem.get_text(separator=" ", strip=True)
            if not texte:
                continue
            results.append(_make_article(art_id_attr, titre, texte, str(elem), celex, nom))
        return results

    def _split_by_article_marker(self, text: str, celex: str, nom: str) -> list[dict]:
        """Fallback : découper un texte brut en articles via regex."""
        # Chercher "Article 1", "Article 25 bis", etc.
        pattern = re.compile(
            r"(?:^|\n)(Article\s+\d+\s*(?:bis|ter|quater)?[a-z]?)"
            r"(?:\s*\n|\s+)",
            re.MULTILINE | re.IGNORECASE,
        )
        parts = pattern.split(text)
        results = []
        # parts : [préambule, titre1, contenu1, titre2, contenu2, ...]
        i = 1
        while i + 1 < len(parts):
            titre = parts[i].strip()
            contenu = parts[i + 1].strip()
            if contenu:
                m = re.search(r"\d+", titre)
                art_id = f"art_{m.group()}" if m else f"art_{i}"
                results.append(_make_article(art_id, titre, f"{titre}\n{contenu}", "", celex, nom))
            i += 2
        return results


# ------------------------------------------------------------------
# Utilitaires
# ------------------------------------------------------------------


def _make_article(
    art_id: str,
    titre: str,
    texte: str,
    texte_html: str,
    celex: str,
    nom: str,
) -> dict:
    return {
        "article_id": f"EURLEX-{celex}-{art_id}",
        "titre": titre,
        "texte": texte,
        "texte_html": texte_html,
        "code_source": nom,
        "date_publication": "",
        "etat": "VIGUEUR",
        "source": "eurlex",
        "celex": celex,
    }
