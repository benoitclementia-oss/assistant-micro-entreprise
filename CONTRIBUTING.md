# Contribuer

Merci de votre intérêt pour ce projet. Voici comment contribuer.

## Signaler un bug

Ouvrez une [issue](https://github.com/benoitclementia-oss/assistant-micro-entreprise/issues) avec :
- Une description claire du problème
- Les étapes pour le reproduire
- Le comportement attendu vs observé

## Proposer une amélioration

1. Ouvrez une issue pour discuter de l'idée
2. Forkez le dépôt
3. Créez une branche (`git checkout -b feature/ma-feature`)
4. Commitez vos changements
5. Ouvrez une Pull Request

## Standards de code

### Python (backend)

```bash
python -m ruff check .      # Lint
python -m ruff format .     # Format
python -m pytest            # Tests
```

Les tests doivent passer et la couverture ne doit pas baisser.

### TypeScript (frontend)

```bash
cd frontend
npm run lint                # ESLint
npm run build               # Vérification TypeScript
```

## Licence

En contribuant, vous acceptez que vos contributions soient sous licence [MIT](LICENSE).
