# Assistant Micro-Entreprise — Frontend

Interface utilisateur de l'assistant juridique Assistant Micro-Entreprise.

## Stack

- **React 19** + TypeScript
- **Vite 7** (build + dev server)
- **Tailwind CSS 4** + **Shadcn/UI** (composants)
- **Lucide React** (icônes)

## Développement

```bash
npm install       # Installer les dépendances
npm run dev       # Serveur de dev → http://localhost:5173 (proxy vers :8000)
npm run build     # Build de production
npm run lint      # Vérification ESLint
npm run preview   # Prévisualiser le build
```

## Composants

| Composant | Rôle |
|---|---|
| `ChatInterface` | Zone de conversation principale |
| `ChatInput` | Saisie de message |
| `Sidebar` | Barre latérale (profil, échéances, documents) |
| `MessageBubble` | Rendu d'un message (Markdown) |
| `LoginPage` | Authentification par mot de passe |
| `WelcomeScreen` | Onboarding premier lancement |
| `ProfilCard` | Carte profil utilisateur |
| `DocumentsCard` | Liste des documents générés |
| `EcheancesCard` | Prochaines échéances |
| `ErrorBanner` | Notification d'erreurs |

## Architecture

```
src/
├── api/client.ts       # Client HTTP (fetch wrapper, proxy vers :8000)
├── components/         # Composants métier + Shadcn/UI (ui/)
├── hooks/              # useChat (messages, envoi), useSidebar (état)
├── types/index.ts      # Interfaces TypeScript
├── lib/utils.ts        # Utilitaires (cn)
├── App.tsx             # Root : auth → onboarding → chat
└── main.tsx            # Point d'entrée
```

Le proxy de développement (Vite) redirige `/api/*` vers `http://localhost:8000` — aucune configuration CORS nécessaire en dev.
