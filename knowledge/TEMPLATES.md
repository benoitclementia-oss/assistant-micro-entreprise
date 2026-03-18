# Index des templates — Assistant Micro-Entreprise

## Templates actifs

Tous les templates utilisent le moteur **Jinja2** et sont stockés dans `../templates/`.

| Template | Fichier | Usage | Variables requises |
|---|---|---|---|
| **Facture** | `facture.md` | Génération de factures micro-entrepreneur | client, prestations, montant, date, numéro |
| **Devis** | `devis.md` | Création de devis | client, prestations, montant, validité |
| **Confirmation** | `confirmation.md` | Confirmation de commande/prestation | client, référence, date |
| **Administratif** | `administratif.md` | Documents administratifs génériques | destinataire, objet, contenu |

## Règles d'utilisation

1. **Ne jamais modifier un template sans validation** — Les templates sont la source de vérité pour le format des documents
2. **Mentions légales obligatoires** — Chaque template doit inclure les mentions légales micro-entrepreneur (SIRET, dispensé de TVA art. 293B CGI)
3. **Numérotation séquentielle** — Format `YYYY-MM-XXX`, ne jamais réutiliser un numéro
4. **Archivage** — Chaque document généré est sauvegardé dans `data/documents/`

## Templates à créer (roadmap)

| Template | Priorité | Usage prévu |
|---|---|---|
| Déclaration de CA | Haute | Aide à la déclaration trimestrielle/mensuelle |
| Relance client | Moyenne | Relance de paiement (J+30, J+45) |
| Contrat de prestation | Moyenne | Modèle de contrat type |
| Attestation de vigilance | Basse | Demande URSSAF |
