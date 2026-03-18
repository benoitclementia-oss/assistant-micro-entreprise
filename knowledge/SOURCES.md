# Sources de connaissances — Assistant Micro-Entreprise

## APIs officielles

| Source | Type | Accès | Statut |
|---|---|---|---|
| **Legifrance PISTE** | API REST | Sandbox (credentials sandbox) | Actif |
| **OpenAI Embeddings** | API | `text-embedding-3-small` | Actif |
| **Qdrant** | Base vectorielle locale | `localhost:6333` | Actif |

### Legifrance — Règles d'utilisation
- Credentials actuels = **SANDBOX uniquement**
- Endpoint cassé : `POST /consult/code` avec `sctId` → ne pas utiliser
- `fond` correct : `LODA_ETAT` ou `CODE_ETAT` (pas `LODA`/`CODE`)
- `typePagination: "DEFAUT"` obligatoire pour les recherches
- Rate limiting : **0.5s minimum entre requêtes**

## Textes juridiques de référence

| Texte | Domaine | Collection Qdrant |
|---|---|---|
| Code Général des Impôts (CGI) | Fiscalité micro-entreprise | `lois_fiscales` |
| Livre des Procédures Fiscales (LPF) | Procédures fiscales | `lois_fiscales` |
| Code de Commerce | Comptabilité, obligations | `regles_comptables` |
| LODA (Lois et décrets en vigueur) | Réglementations administratives | `reglementations_administratives` |

## Collections Qdrant

| Collection | Dimensions | Métrique | Sources |
|---|---|---|---|
| `lois_fiscales` | 1536 | Cosine | CGI + LPF |
| `regles_comptables` | 1536 | Cosine | Code de commerce + LODA |
| `reglementations_administratives` | 1536 | Cosine | Recherches LODA micro-entreprise |

## Bases de données locales

| Base | Rôle | Chemin |
|---|---|---|
| `assistant-micro-entreprise.db` | État de l'agent, profils, historique | `data/assistant-micro-entreprise.db` |
| `calendar.db` | Échéances, calendrier fiscal | `data/calendar.db` |

## Cache local

Les résultats d'ingestion sont cachés dans `data/cache/` au format JSON pour éviter les appels API redondants.
