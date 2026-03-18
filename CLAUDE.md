# Assistant Micro-Entreprise — Guide de développement

## Stack technique

- **Python 3.12+** — Backend et pipeline d'ingestion
- **FastAPI** — API REST (port 8000)
- **React 19 + TypeScript + Vite + Shadcn/UI** — Frontend (port 5173)
- **Qdrant** sur Docker (`localhost:6333`) — base vectorielle, cosine, 1536 dimensions
- **OpenAI** `text-embedding-3-small` pour les embeddings
- **API Legifrance** (plateforme PISTE) pour les textes juridiques
- **Jinja2** pour les templates de documents

## Structure

```
├── agent/          # Agent IA (LLM, RAG, mémoire, calendrier, documents, email)
├── api/            # FastAPI : /chat, /profil, /documents, /echeances, /sidebar
├── frontend/src/   # React (ChatInterface, Sidebar, Cards)
├── scripts/        # Pipeline d'ingestion : Legifrance/EUR-Lex/PDF → Qdrant
├── templates/      # Templates Jinja2 (facture, devis, confirmation)
├── tests/          # Tests pytest
└── knowledge/      # Documentation des sources juridiques
```

## Commandes

```bash
# Services Docker (Qdrant + n8n)
docker compose up -d

# API backend
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Tests + couverture
python -m pytest

# Qualité de code
python -m ruff check .
python -m ruff format .

# Frontend
cd frontend && npm run dev
cd frontend && npm run lint
cd frontend && npm run build
```

## API Legifrance — PISTE Sandbox

Les credentials actuels sont pour l'environnement **sandbox** uniquement.

| Endpoint | Payload | Notes |
|---|---|---|
| `POST /consult/code/tableMatieres` | `{"textId": "...", "date": "YYYY-MM-DD"}` | `date` obligatoire |
| `POST /consult/getArticle` | `{"id": "LEGIARTI..."}` | Retourne le texte complet |
| `POST /search` | `{"fond": "LODA_ETAT", ...}` | Fonds = `LODA_ETAT` ou `CODE_ETAT`. `typePagination: "DEFAUT"` |

Endpoint cassé sur sandbox : `POST /consult/code` (avec `sctId`) → 500 — ne pas utiliser.

## Règles

- Ne jamais commiter le `.env`
- Toujours tester en `--dry-run` avant une ingestion réelle
- Rate limiting : 0.5s entre requêtes API Legifrance
- Shadcn/UI pour tous les composants frontend
