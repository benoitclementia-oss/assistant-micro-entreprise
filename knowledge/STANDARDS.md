# Normes et bonnes pratiques — Assistant Micro-Entreprise

## Conformité légale obligatoire

### RGPD (Règlement Général sur la Protection des Données)
- **Art. 5** — Principes de traitement (licéité, minimisation, exactitude)
- **Art. 25** — Protection des données dès la conception (Privacy by Design)
- **Art. 30** — Registre des traitements
- **Art. 32-34** — Sécurité du traitement, notification de violations
- **Application** : Toute donnée client (profil, documents) doit être stockée localement, chiffrée, avec consentement explicite

### Code de Commerce
- **Art. L123-22** — Conservation des documents comptables pendant **10 ans**
- **Application** : Les factures et devis générés doivent être archivés avec horodatage

### Réglementation IA (IA Act — Règlement 2024/1689)
- Classification du système : **risque limité** (assistant administratif)
- **Obligation de transparence** : L'utilisateur doit savoir qu'il interagit avec une IA
- **Application** : Mention obligatoire dans les documents générés

## Normes de sécurité

### ISO 27001 (Système de Management de la Sécurité de l'Information)
- Contrôle d'accès aux données juridiques
- Journalisation des actions (audit trail)
- Chiffrement des données au repos et en transit

### OWASP Top 10
- Validation des entrées utilisateur (injection SQL, XSS)
- Authentification sécurisée des endpoints API
- Protection contre les injections de prompts (prompt injection)

## Bonnes pratiques métier

### Génération de documents
- Utiliser **exclusivement** les templates approuvés dans `templates/`
- Chaque document généré doit contenir : date, destinataire, numéro unique, mentions légales
- Format de numérotation : `YYYY-MM-XXX` (année-mois-séquentiel)

### RAG (Retrieval Augmented Generation)
- Chunking : ~800 tokens par segment
- Toujours citer la source juridique exacte (article, alinéa)
- Ne jamais inventer de référence légale — si le contexte RAG ne contient pas la réponse, le dire
- Score de confiance minimum pour les réponses : documenter l'incertitude

### Calendrier fiscal
- Vérifier les échéances contre le calendrier officiel de la DGFiP
- Alertes : J-30, J-15, J-7, J-1 avant chaque échéance
- Distinguer régime micro-BNC et micro-BIC (seuils différents)
