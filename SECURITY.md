# Politique de sécurité

## Signaler une vulnérabilité

Si vous découvrez une faille de sécurité, **ne créez pas d'issue publique**. Contactez-nous directement par email à l'adresse indiquée dans le profil de l'organisation.

## Secrets et configuration

- **Ne jamais commiter le fichier `.env`** — il est exclu par `.gitignore`
- Copier `.env.example` vers `.env` et y renseigner vos propres clés
- Les credentials Legifrance actuels sont pour l'environnement **sandbox** (pas production)
- Le mot de passe d'application Gmail (`GMAIL_APP_PASSWORD`) est optionnel

## Bonnes pratiques appliquées

- Toutes les clés API sont chargées depuis les variables d'environnement
- Aucun secret codé en dur dans le code source
- Authentification par mot de passe sur l'interface web
- CORS configuré côté FastAPI
- Base SQLite locale (pas d'exposition réseau)
