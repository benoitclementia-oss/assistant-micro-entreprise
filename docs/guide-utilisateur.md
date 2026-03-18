# Guide Utilisateur — Assistant Micro-Entreprise

## Présentation ?

Assistant Micro-Entreprise est votre **assistant juridique et administratif** specialise pour les micro-entreprises (auto-entrepreneurs) en France. Il vous aide a :

- Repondre a vos questions sur la **fiscalite**, la **comptabilite** et les **obligations administratives**
- Generer des **documents professionnels** (factures, devis, lettres)
- Gerer votre **calendrier d'echeances** fiscales et sociales
- Envoyer des **emails professionnels**

## Demarrage rapide

### 1. Lancer Assistant Micro-Entreprise

```bash
docker compose up -d
```

Ouvrez ensuite votre navigateur a l'adresse : **http://localhost**

### 2. Se connecter

Entrez le mot de passe que vous avez defini dans la configuration (variable `APP_PASSWORD`).

### 3. Configurer votre profil

Au premier lancement, un ecran de bienvenue vous guide en 3 etapes :
1. **Vos coordonnees** : prenom, nom, email, telephone
2. **Votre entreprise** : nom, SIRET, activite, regime fiscal
3. **Votre adresse** : adresse professionnelle

Ces informations servent a pre-remplir automatiquement vos documents (factures, devis...).

Vous pouvez mettre a jour votre profil a tout moment :
> "Mon adresse a change, c'est maintenant 12 rue de la Paix, 75002 Paris"

## Comment utiliser Assistant Micro-Entreprise

### Poser des questions juridiques

L'assistant recherche dans sa base de textes de loi francais avant de repondre. Il cite toujours les articles pertinents.

**Exemples :**
- "Quels sont les seuils de chiffre d'affaires pour un micro-BNC ?"
- "Quelles sont mes obligations de facturation ?"
- "Comment fonctionne la TVA pour un auto-entrepreneur ?"

### Generer des documents

L'assistant peut creer des factures, devis, confirmations et lettres administratives.

**Exemple :**
> "Prepare-moi une facture pour mon client Martin SARL, prestation de conseil informatique, 500 euros"

L'assistant vous montrera un brouillon. Repondez "OK" ou "c'est bon" pour confirmer et sauvegarder le document.

### Gerer vos echeances

Les echeances fiscales et sociales sont pre-configurees (declarations URSSAF, CFE, declaration de revenus).

**Exemples :**
- "Quelles sont mes prochaines echeances ?"
- "Ajoute une echeance : rendez-vous comptable le 15 avril"

Les echeances apparaissent dans la barre laterale a gauche. Cochez-les quand elles sont faites.

### Envoyer des emails

Si la fonction email est configuree, L'assistant peut envoyer des emails pour vous.

**Exemple :**
> "Envoie un email a client@example.com pour confirmer notre rendez-vous de lundi"

L'assistant vous demandera toujours confirmation avant d'envoyer.

## Interface

### La barre laterale (a gauche)

- **Profil** : resume de vos informations
- **Echeances** : vos prochaines dates importantes (cochez quand c'est fait)
- **Documents** : vos documents generes (cliquez pour les consulter)
- **+ Nouvelle conversation** : recommencer une discussion vierge

Sur mobile, la barre laterale est cachee. Appuyez sur le bouton menu (trois barres) en haut a gauche pour l'ouvrir.

### Le chat (au centre)

C'est ici que vous discutez avec l'assistant. Tapez votre message et appuyez sur Entree.

**Astuce :** Pour aller a la ligne sans envoyer, utilisez **Maj + Entree**.

## En cas de probleme

| Probleme | Solution |
|---|---|
| "Impossible de contacter le serveur" | Verifiez que `docker compose up -d` tourne bien |
| "Service temporairement indisponible" | Un redemarrage de Docker devrait resoudre le probleme |
| "La requete a mis trop de temps" | Reformulez votre question plus simplement |
| "Session expiree" | Rechargez la page et reconnectez-vous |

## Donnees et confidentialite

- Toutes vos donnees restent **sur votre ordinateur** (base de donnees locale)
- Les questions juridiques sont envoyees a OpenAI pour obtenir des reponses intelligentes
- Aucune donnee n'est partagee avec des tiers
- Votre mot de passe protege l'acces a l'interface
