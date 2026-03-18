"""Client PDF — téléchargement et extraction de texte depuis des PDFs publics.

Stratégie de découpage en sections :
  1. Détection des titres numérotés  (ex: "1.", "1.1", "2.3.4")
  2. Détection des marqueurs "Article N"
  3. Détection des lignes en MAJUSCULES (titres de chapitres)
  4. Fallback : une section = une page

Chaque section devient un "article" au sens Assistant Micro-Entreprise :
  {article_id, titre, texte, code_source, etat, source, source_tag}
"""

import hashlib
import io
import logging
import re
import time
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

_REQUEST_DELAY = 2.0  # secondes — politesse
_MIN_SECTION_CHARS = 80  # ignorer les micro-sections

# Dossier local pour les PDFs téléchargés manuellement
# (fallback si le téléchargement automatique échoue)
_LOCAL_PDF_DIR = Path(__file__).resolve().parent.parent / "data" / "pdfs"


class PdfClient:
    def __init__(self) -> None:
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (compatible; MicroEntreprise-LegalBot/1.0; "
                    "+https://github.com/research)"
                ),
                "Accept": "application/pdf,*/*",
            }
        )
        self._last_request_time: float = 0

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    def _download(self, url: str) -> bytes:
        elapsed = time.time() - self._last_request_time
        if elapsed < _REQUEST_DELAY:
            time.sleep(_REQUEST_DELAY - elapsed)
        logger.info("  Téléchargement : %s", url)
        resp = self._session.get(url, timeout=60, stream=True)
        self._last_request_time = time.time()
        resp.raise_for_status()
        return resp.content

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def fetch_document(self, url: str, nom: str, source_tag: str) -> list[dict]:
        """Télécharger un PDF et retourner ses sections comme articles Assistant Micro-Entreprise.

        Priorité :
          1. Fichier local dans data/pdfs/{source_tag}.pdf (si présent)
          2. Téléchargement depuis l'URL

        Returns:
            Liste de dicts {article_id, titre, texte, texte_html,
            code_source, date_publication, etat, source, source_tag}
        """
        # 1. Fichier local (bypass anti-bot)
        local_path = _LOCAL_PDF_DIR / f"{source_tag}.pdf"
        if local_path.exists():
            logger.info("  Fichier local trouvé : %s", local_path.name)
            pdf_bytes = local_path.read_bytes()
        else:
            # 2. Téléchargement distant
            try:
                pdf_bytes = self._download(url)
            except requests.exceptions.HTTPError as exc:
                logger.error("Erreur HTTP PDF %s : %s", url, exc)
                logger.info(
                    "  → Déposez le PDF manuellement dans : %s",
                    _LOCAL_PDF_DIR / f"{source_tag}.pdf",
                )
                return []
            except requests.exceptions.RequestException as exc:
                logger.error("Erreur réseau PDF %s : %s", url, exc)
                logger.info(
                    "  → Déposez le PDF manuellement dans : %s",
                    _LOCAL_PDF_DIR / f"{source_tag}.pdf",
                )
                return []

        pages = self._extract_pages(pdf_bytes)
        if not pages:
            logger.warning("Aucun texte extrait depuis %s", url)
            return []

        sections = self._split_into_sections(pages)
        articles = []
        for i, (titre, texte) in enumerate(sections, 1):
            if len(texte) < _MIN_SECTION_CHARS:
                continue
            section_id = f"s{i:04d}"
            uid = hashlib.md5(f"{source_tag}-{section_id}".encode()).hexdigest()[:12]
            articles.append(
                {
                    "article_id": f"PDF-{source_tag}-{uid}",
                    "titre": titre,
                    "texte": texte,
                    "texte_html": "",
                    "code_source": nom,
                    "date_publication": "",
                    "etat": "VIGUEUR",
                    "source": "pdf",
                    "source_tag": source_tag,
                }
            )

        logger.info("  %d sections extraites depuis '%s'", len(articles), nom)
        return articles

    # ------------------------------------------------------------------
    # Extraction du texte PDF
    # ------------------------------------------------------------------

    def _extract_pages(self, pdf_bytes: bytes) -> list[str]:
        """Extraire le texte page par page avec pypdf."""
        try:
            import pypdf
        except ImportError as err:
            raise ImportError("pypdf non installé. Lancez : pip install pypdf") from err

        pages: list[str] = []
        try:
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                text = page.extract_text() or ""
                pages.append(text)
        except Exception as exc:
            logger.error("Erreur lecture PDF : %s", exc)
        return pages

    # ------------------------------------------------------------------
    # Découpage en sections
    # ------------------------------------------------------------------

    def _split_into_sections(self, pages: list[str]) -> list[tuple[str, str]]:
        """Découper le texte en sections logiques.

        Retourne une liste de (titre, texte).
        """
        full_text = "\n".join(pages)
        sections = (
            self._split_by_numbered_headings(full_text)
            or self._split_by_article_markers(full_text)
            or self._split_by_caps_headings(full_text)
            or self._split_by_pages(pages)
        )
        return sections

    # Stratégie 1 : titres numérotés (1., 1.1, 1.2.3, ...)
    _RE_NUMBERED = re.compile(
        r"(?:^|\n)(\d{1,2}(?:\.\d{1,2}){0,3}\.?\s+[A-ZÀÂÉÈÊËÎÏÔÙÛÜ][^\n]{3,80})\n",
        re.MULTILINE,
    )

    def _split_by_numbered_headings(self, text: str) -> list[tuple[str, str]]:
        parts = self._RE_NUMBERED.split(text)
        if len(parts) < 5:  # pas assez de sections trouvées
            return []
        return self._assemble_sections(parts, min_count=3)

    # Stratégie 2 : "Article N" (documents réglementaires)
    _RE_ARTICLE = re.compile(
        r"(?:^|\n)(Article\s+\d+[a-z]?(?:\s*[-–]\s*[^\n]{0,60})?)\n",
        re.MULTILINE | re.IGNORECASE,
    )

    def _split_by_article_markers(self, text: str) -> list[tuple[str, str]]:
        parts = self._RE_ARTICLE.split(text)
        if len(parts) < 5:
            return []
        return self._assemble_sections(parts, min_count=3)

    # Stratégie 3 : lignes en MAJUSCULES (chapitres)
    _RE_CAPS = re.compile(
        r"(?:^|\n)([A-ZÀÂÉÈÊËÎÏÔÙÛÜ][A-ZÀÂÉÈÊËÎÏÔÙÛÜ\s\-]{5,70})\n",
        re.MULTILINE,
    )

    def _split_by_caps_headings(self, text: str) -> list[tuple[str, str]]:
        parts = self._RE_CAPS.split(text)
        if len(parts) < 5:
            return []
        return self._assemble_sections(parts, min_count=3)

    # Stratégie 4 : fallback page par page
    def _split_by_pages(self, pages: list[str]) -> list[tuple[str, str]]:
        result = []
        for i, page_text in enumerate(pages, 1):
            text = page_text.strip()
            if not text:
                continue
            # Utiliser la première ligne non-vide comme titre
            first_line = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
            titre = first_line[:80] if first_line else f"Page {i}"
            result.append((titre, text))
        return result

    # ------------------------------------------------------------------
    # Utilitaire : reconstituer (titre, contenu) depuis les parties regex
    # ------------------------------------------------------------------

    @staticmethod
    def _assemble_sections(parts: list[str], min_count: int = 3) -> list[tuple[str, str]]:
        """Reconstituer les sections depuis un split regex.

        parts alterne : [préambule, titre1, contenu1, titre2, contenu2, ...]
        """
        sections: list[tuple[str, str]] = []

        # Préambule (avant le premier titre)
        preambule = parts[0].strip()
        if len(preambule) >= _MIN_SECTION_CHARS:
            sections.append(("Introduction / Préambule", preambule))

        i = 1
        while i + 1 < len(parts):
            titre = parts[i].strip()
            contenu = parts[i + 1].strip()
            if titre:
                sections.append((titre, f"{titre}\n\n{contenu}"))
            i += 2

        if len(sections) < min_count:
            return []
        return sections
