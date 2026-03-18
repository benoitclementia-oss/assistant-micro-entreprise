# Assistant Micro-Entreprise — Assistant Juridique IA

[![CI — Tests & Qualité](https://github.com/benoitclementia-oss/assistant-micro-entreprise/actions/workflows/ci.yml/badge.svg)](https://github.com/benoitclementia-oss/assistant-micro-entreprise/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![React 19](https://img.shields.io/badge/react-19-61DAFB.svg)](https://react.dev)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Assistant IA spécialisé dans le droit français des micro-entreprises. Il ingère les textes de loi officiels (Legifrance, EUR-Lex, CNIL, ANSSI), les découpe en fragments sémantiques, les vectorise, puis les utilise via RAG (Retrieval-Augmented Generation) pour répondre aux questions juridiques, fiscales et administratives des micro-entrepreneurs.

> Assistant IA open-source pour les micro-entrepreneurs français.

---

## Fonctionnalités

| Fonctionnalité | Description |
|---|---|
| **Recherche juridique RAG** | Interrogation en langage naturel sur 12 collections de textes de loi |
| **Génération de documents** | Factures, devis, confirmations, courriers administratifs (templates Jinja2) |
| **Calendrier d'échéances** | Suivi des deadlines fiscales, sociales et personnalisées |
| **Mémoire persistante** | L'agent retient les informations métier entre les sessions |
| **Profil utilisateur** | Données d'entreprise auto-injectées dans les documents générés |
| **Email** | Envoi de documents par Gmail depuis l'interface |

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  React 19   │────▶│  FastAPI      │────▶│  GPT-4o         │
│  TypeScript │◀────│  (port 8000)  │◀────│  Function Calling│
│  Shadcn/UI  │     │              │     └────────┬────────┘
│  (port 5173)│     │  Routers:    │              │
└─────────────┘     │  /chat       │     ┌────────▼────────┐
                    │  /profil     │     │  Qdrant          │
                    │  /documents  │     │  (vectorielle)   │
                    │  /echeances  │     │  12 collections  │
                    │  /sidebar    │     │  1536 dim cosine │
                    └──────────────┘     └─────────────────┘
                                                  ▲
                                         ┌────────┴────────┐
                                         │  Pipeline        │
                                         │  d'ingestion     │
                                         │  Legifrance      │
                                         │  EUR-Lex         │
                                         │  PDF (ANSSI,CNIL)│
                                         └─────────────────┘
```

## Stack technique

| Couche | Technologies |
|---|---|
| **Frontend** | React 19, TypeScript, Vite 7, Tailwind CSS 4, Shadcn/UI |
| **Backend** | Python 3.12+, FastAPI, Uvicorn |
| **IA / LLM** | OpenAI GPT-4o (function calling), text-embedding-3-small |
| **Base vectorielle** | Qdrant (Docker, cosine, 1536 dimensions) |
| **Sources juridiques** | API Legifrance PISTE, EUR-Lex, PDF ANSSI/CNIL/ENISA |
| **Documents** | Jinja2 (factures, devis, confirmations, administratif) |
| **Infrastructure** | Docker Compose (4 services) |

## Collections de données juridiques

| Collection | Sources | Usage |
|---|---|---|
| `lois_fiscales` | CGI + LPF | Fiscalité micro-entreprise |
| `regles_comptables` | Code de commerce + LODA | Comptabilité |
| `reglementations_administratives` | LODA micro-entreprise | Démarches administratives |
| `droit_consommation` | Code de la consommation | CGV, garanties, médiation |
| `securite_sociale_micro` | LODA cotisations/ACRE/retraite | Protection sociale |
| `guides_cnil_tpe` | Guides CNIL (PDF) | Conformité RGPD |
| `numerique_ia_securite` | LODA signature, cybersécurité, IA | Numérique & sécurité |
| `reglements_europeens` | RGPD, eIDAS, Cyber Resilience Act | Réglementations UE |
| `certifications_securite` | ANSSI, ENISA, CNIL (PDF) | Certifications sécurité |
| `artisanat_reglemente` | Code de l'artisanat + LODA | Pack Artisanat |
| `hygiene_alimentaire` | Règlements UE 178/852/853 + LODA | Pack HACCP |
| `accessibilite_pmr` | LODA accessibilité ERP/bâtiments | Pack Accessibilité PMR |

## Installation

### Prérequis

- Python 3.12+
- Node.js 22+
- Docker & Docker Compose
- Clés API : OpenAI, Legifrance PISTE (sandbox)

### 1. Cloner et configurer

```bash
git clone https://github.com/benoitclementia-oss/assistant-micro-entreprise.git
cd assistant-micro-entreprise

# Créer le fichier de secrets (ne sera jamais commité)
cp .env.example .env
# Remplir les clés dans .env
```

### 2. Lancer les services

```bash
# Démarrer Qdrant + n8n
docker compose up -d

# Installer les dépendances Python
pip install -r requirements.txt

# Lancer le serveur API
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Ingérer les textes juridiques

```bash
# Test à blanc (sans appel API ni écriture)
python -m scripts.ingest --dry-run

# Ingestion complète
python -m scripts.ingest

# Une seule collection
python -m scripts.ingest --collection lois_fiscales
```

### 4. Lancer le frontend

```bash
cd frontend
npm install
npm run dev    # → http://localhost:5173
```

### 5. Déploiement Docker complet

```bash
docker compose up -d --build    # 4 services : Qdrant, n8n, backend, frontend
```

## Développement

### Tests

```bash
# Installer les dépendances de dev
pip install -r requirements-dev.txt

# Lancer les tests avec couverture
python -m pytest

# Un seul fichier de test
python -m pytest tests/test_documents.py

# Exclure les tests lents
python -m pytest -m "not slow"

# Les rapports sont générés dans reports/
#   reports/junit.xml          — résultats JUnit (CI)
#   reports/coverage.json      — couverture en JSON
#   reports/coverage.xml       — couverture en XML (CI)
#   reports/coverage_html/     — rapport visuel navigable
```

### Qualité de code

```bash
# Vérifier le style et les erreurs
ruff check .

# Formater automatiquement
ruff format .

# Vérification de types (mode progressif)
mypy agent/ api/ scripts/ --ignore-missing-imports
```

### Frontend

```bash
cd frontend
npm run lint       # ESLint
npm run build      # Build de production
```

## Structure du projet

```
assistant-micro-entreprise/
├── agent/                  # Agent IA (LLM, RAG, mémoire, calendrier, documents)
│   ├── llm.py              # GPT-4o avec function calling (11 outils)
│   ├── rag.py              # Recherche vectorielle Qdrant + formatage citations
│   ├── memory.py           # Mémoire persistante (faits, sessions)
│   ├── documents.py        # Génération de documents (brouillon → confirmation)
│   ├── calendar_manager.py # Échéances fiscales/sociales/custom
│   ├── profile.py          # Profil utilisateur (CRUD)
│   └── tools.py            # Schémas des 11 outils OpenAI
├── api/                    # Backend FastAPI
│   ├── main.py             # App, CORS, auth middleware, lifespan
│   ├── models.py           # Modèles Pydantic (requêtes/réponses)
│   ├── deps.py             # Injection de dépendances
│   └── routers/            # Endpoints : chat, auth, documents, échéances, profil
├── scripts/                # Pipeline d'ingestion
│   ├── ingest.py           # Orchestrateur : fetch → chunk → embed → Qdrant
│   ├── legifrance_client.py# Client API Legifrance (OAuth2, rate limiting)
│   ├── eurlex_client.py    # Client EUR-Lex
│   ├── pdf_client.py       # Extraction de texte PDF
│   ├── embedding.py        # Chunking (~800 tokens) + embeddings OpenAI
│   ├── qdrant_loader.py    # Upsert batch Qdrant (IDs déterministes MD5)
│   └── config.py           # Configuration des 12 collections
├── frontend/               # Interface React
│   └── src/
│       ├── components/     # ChatInterface, Sidebar, Cards, Shadcn/UI
│       ├── hooks/          # useChat, useSidebar
│       └── api/client.ts   # Client HTTP
├── templates/              # Templates Jinja2 (facture, devis, confirmation)
├── tests/                  # 105 tests pytest
├── reports/                # Rapports de test et couverture (générés)
├── docs/                   # Guide utilisateur
├── knowledge/              # Sources juridiques, standards, templates
├── docker-compose.yml      # Qdrant + n8n + backend + frontend
├── Dockerfile.backend      # Image Python 3.12
├── pyproject.toml          # Config pytest, ruff, mypy, coverage
├── requirements.txt        # Dépendances production
└── requirements-dev.txt    # Dépendances développement
```

## Outils de l'agent (Function Calling)

L'agent dispose de **11 outils** appelables par GPT-4o :

| Outil | Description |
|---|---|
| `recherche_juridique` | Recherche RAG dans les collections Qdrant |
| `preparer_document` | Créer un brouillon (facture, devis, etc.) |
| `confirmer_document` | Sauvegarder un brouillon validé |
| `lister_documents` | Lister les documents générés |
| `lister_echeances` | Afficher les prochaines échéances |
| `ajouter_echeance` | Ajouter une échéance au calendrier |
| `envoyer_email` | Envoyer un document par email |
| `memoriser` | Sauvegarder un fait pour les sessions futures |
| `rappeler` | Rechercher dans la mémoire |
| `consulter_profil` | Lire le profil utilisateur |
| `modifier_profil` | Mettre à jour les données d'entreprise |

## Variables d'environnement

| Variable | Requis | Description |
|---|---|---|
| `LEGIFRANCE_CLIENT_ID` | Oui | Client ID PISTE (sandbox ou production) |
| `LEGIFRANCE_CLIENT_SECRET` | Oui | Client secret PISTE |
| `OPENAI_API_KEY` | Oui | Clé API OpenAI |
| `QDRANT_URL` | Non | URL Qdrant (défaut : `http://localhost:6333`) |
| `GMAIL_ADDRESS` | Non | Adresse Gmail pour l'envoi d'emails |
| `GMAIL_APP_PASSWORD` | Non | Mot de passe d'application Gmail |
| `APP_PASSWORD` | Non | Mot de passe d'accès à l'interface |

## Licence

[MIT](LICENSE) — Copyright (c) 2026 benoitclementia-oss
