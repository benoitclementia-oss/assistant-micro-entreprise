import os
from pathlib import Path

from dotenv import load_dotenv

# Charger le .env depuis la racine du projet
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


def _require(var: str) -> str:
    val = os.getenv(var)
    if not val:
        raise RuntimeError(f"Variable d'environnement manquante : {var}")
    return val


LEGIFRANCE_CLIENT_ID = _require("LEGIFRANCE_CLIENT_ID")
LEGIFRANCE_CLIENT_SECRET = _require("LEGIFRANCE_CLIENT_SECRET")
OPENAI_API_KEY = _require("OPENAI_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

# Gmail (optionnel — pour l'envoi d'emails par l'agent)
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")

# Constantes embeddings
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536

# Collections Qdrant et codes Legifrance associes
COLLECTIONS = {
    "lois_fiscales": {
        "codes": [
            {"id": "LEGITEXT000006069577", "nom": "Code general des impots"},
            {"id": "LEGITEXT000006069583", "nom": "Livre des procedures fiscales"},
        ],
        "recherches_loda": [],
    },
    "regles_comptables": {
        "codes": [
            {"id": "LEGITEXT000005634379", "nom": "Code de commerce"},
        ],
        "recherches_loda": ["normes comptables"],
    },
    "reglementations_administratives": {
        "codes": [],
        "recherches_loda": [
            "micro-entreprise",
            "auto-entrepreneur",
        ],
    },
    "numerique_ia_securite": {
        # Pas de codes entiers (quota sandbox limité).
        # Code civil articles 1366-1367 et LIL sont couverts via recherches LODA.
        "codes": [],
        # Recherches LODA ciblées : lois, décrets, arrêtés en vigueur
        "recherches_loda": [
            "signature électronique",
            "identité numérique",
            "cybersécurité",
            "intelligence artificielle",
            "protection des données personnelles",
            "loi informatique libertés",
            "preuve écrit électronique",
        ],
    },
    "reglements_europeens": {
        # Textes EUR-Lex uniquement (pas de source Legifrance)
        "codes": [],
        "recherches_loda": [],
        "eurlex_sources": [
            {"celex": "32016R0679", "nom": "RGPD — Règlement (UE) 2016/679"},
            {"celex": "32014R0910", "nom": "eIDAS — Règlement (UE) 910/2014"},
            {"celex": "32024R1183", "nom": "eIDAS 2.0 — Règlement (UE) 2024/1183"},
            {"celex": "32024R2847", "nom": "Cyber Resilience Act — Règlement (UE) 2024/2847"},
        ],
    },
    "certifications_securite": {
        # Documents PDF publics — ANSSI, ENISA, CNIL
        # URLs vérifiées en mars 2026
        "codes": [],
        "recherches_loda": [],
        "pdf_sources": [
            {
                "url": "https://cyber.gouv.fr/sites/default/files/2022-10/RGS_v-2-00_Corps_du_texte.pdf",
                "nom": "RGS v2.0 — Référentiel Général de Sécurité (ANSSI)",
                "source_tag": "ANSSI-RGS",
            },
            {
                "url": "https://cyber.gouv.fr/sites/default/files/2022-10/RGS_v-2-0_A1.pdf",
                "nom": "RGS v2.0 Annexe A1 — Règles certificats électroniques (ANSSI)",
                "source_tag": "ANSSI-RGS-A1",
            },
            {
                "url": "https://cyber.gouv.fr/sites/default/files/document/secnumcloud-referentiel-exigences-v3.2.pdf",
                "nom": "SecNumCloud v3.2 — Référentiel d'exigences (ANSSI)",
                "source_tag": "ANSSI-SecNumCloud",
            },
            {
                "url": "https://cyber.gouv.fr/sites/default/files/document/PRIS_Referentiel-exigences_v3.2.pdf",
                "nom": "PRIS v3.2 — Prestataires de Réponse aux Incidents (ANSSI)",
                "source_tag": "ANSSI-PRIS",
            },
            {
                "url": "https://cyber.gouv.fr/sites/default/files/2017/01/guide_hygiene_informatique_anssi.pdf",
                "nom": "Guide d'hygiène informatique — 42 mesures (ANSSI)",
                "source_tag": "ANSSI-Hygiene",
            },
            {
                "url": "https://www.enisa.europa.eu/sites/default/files/2025-06/ENISA_Technical_implementation_guidance_on_cybersecurity_risk_management_measures_version_1.0.pdf",
                "nom": "NIS2 Technical Implementation Guidance v1.0 (ENISA)",
                "source_tag": "ENISA-NIS2-TIG",
            },
            {
                "url": "https://www.enisa.europa.eu/sites/default/files/publications/Cloud%20Security%20Guide%20for%20SMEs.pdf",
                "nom": "Cloud Security Guide for SMEs (ENISA)",
                "source_tag": "ENISA-Cloud-SME",
            },
            {
                "url": "https://www.cnil.fr/sites/default/files/2025-07/ia_liste_de_verification.pdf",
                "nom": "Liste de vérification IA — RGPD (CNIL)",
                "source_tag": "CNIL-IA-Checklist",
            },
        ],
    },
    # ================================================================
    # PACKS COMMERCIAUX — Collections dédiées aux packs thématiques
    # ================================================================
    #
    # Pack 1 : Micro-Entrepreneur
    # Collections utilisées : lois_fiscales, regles_comptables,
    #   reglementations_administratives, reglements_europeens (RGPD),
    #   + les 3 collections ci-dessous
    # ----------------------------------------------------------------
    "droit_consommation": {
        # Code de la consommation — CGV, médiation, rétractation,
        # garanties, pratiques commerciales
        "codes": [
            {"id": "LEGITEXT000006069565", "nom": "Code de la consommation"},
        ],
        "recherches_loda": [],
    },
    "securite_sociale_micro": {
        # Protection sociale du micro-entrepreneur :
        # cotisations, ACRE, indemnités, retraite
        # Le CSS entier est trop volumineux → recherches LODA ciblées
        "codes": [],
        "recherches_loda": [
            "cotisations travailleur indépendant",
            "aide création reprise entreprise ACRE",
            "indemnités journalières travailleur indépendant",
            "retraite travailleur indépendant",
            "protection sociale indépendant",
            "cotisation foncière des entreprises",
        ],
    },
    "guides_cnil_tpe": {
        # Guides pratiques CNIL pour TPE/PME — conformité RGPD
        "codes": [],
        "recherches_loda": [],
        "pdf_sources": [
            {
                "url": "https://www.cnil.fr/sites/default/files/2024-03/guide_de_la_securite_des_donnees_personnelles_-_ed._2024.pdf",
                "nom": "Guide sécurité des données personnelles — 25 fiches (CNIL 2024)",
                "source_tag": "CNIL-Guide-Securite-2024",
            },
            {
                "url": "https://www.cnil.fr/sites/default/files/2024-09/guide_pratique_-_les_bases_legales.pdf",
                "nom": "Guide pratique — Les bases légales du RGPD (CNIL)",
                "source_tag": "CNIL-Bases-Legales",
            },
        ],
    },
    # ----------------------------------------------------------------
    # Pack 2 : Artisanat Réglementé
    # ----------------------------------------------------------------
    "artisanat_reglemente": {
        # Code de l'artisanat (consolidé en 2023, très stable)
        # + textes sur les qualifications artisanales
        "codes": [
            {"id": "LEGITEXT000006075116", "nom": "Code de l'artisanat"},
        ],
        "recherches_loda": [
            "qualification artisanale",
            "répertoire des métiers",
            "chambre de métiers et de l'artisanat",
            "assurance décennale artisan",
        ],
    },
    # ----------------------------------------------------------------
    # Pack 3 : HACCP & Hygiène Alimentaire
    # ----------------------------------------------------------------
    "hygiene_alimentaire": {
        # Réglements EU du « Paquet Hygiène » + textes français
        "codes": [],
        "recherches_loda": [
            "hygiène alimentaire",
            "sécurité sanitaire des aliments",
            "plan de maîtrise sanitaire",
            "formation hygiène alimentaire restauration",
        ],
        "eurlex_sources": [
            {"celex": "32002R0178", "nom": "Food Law — Règlement (CE) 178/2002"},
            {
                "celex": "32004R0852",
                "nom": "Hygiène denrées alimentaires — Règlement (CE) 852/2004",
            },
            {
                "celex": "32004R0853",
                "nom": "Hygiène produits d'origine animale — Règlement (CE) 853/2004",
            },
        ],
    },
    # ----------------------------------------------------------------
    # Pack 4 : Accessibilité PMR (Personnes à Mobilité Réduite)
    # ----------------------------------------------------------------
    "accessibilite_pmr": {
        # Normes d'accessibilité ERP, logements, espaces publics
        # Le CCH entier est trop volumineux → LODA ciblées
        "codes": [],
        "recherches_loda": [
            "accessibilité personnes handicapées établissement recevant public",
            "accessibilité bâtiment neuf",
            "accessibilité bâtiment existant",
            "agenda d'accessibilité programmée",
            "diagnostic accessibilité",
        ],
    },
}
