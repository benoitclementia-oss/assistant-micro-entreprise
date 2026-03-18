"""Définitions des tools pour GPT-4o function calling."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "recherche_juridique",
            "description": (
                "Rechercher dans la base de textes juridiques français "
                "(codes, lois, décrets) indexés dans Qdrant. "
                "Utiliser pour toute question sur le droit fiscal, comptable "
                "ou les réglementations des micro-entreprises."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "La requête de recherche en langage naturel.",
                    },
                    "collections": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
                                "lois_fiscales",
                                "regles_comptables",
                                "reglementations_administratives",
                            ],
                        },
                        "description": (
                            "Collections dans lesquelles chercher. "
                            "Si omis, cherche dans toutes les collections."
                        ),
                    },
                },
                "required": ["query"],
            },
        },
    },
    # --- Documents (brouillon / confirmation) ---
    {
        "type": "function",
        "function": {
            "name": "preparer_document",
            "description": (
                "Préparer un brouillon de document administratif ou commercial. "
                "Le brouillon est retourné pour vérification AVANT sauvegarde. "
                "Utiliser confirmer_document() ensuite pour finaliser."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["facture", "devis", "confirmation", "administratif"],
                        "description": "Le type de document à préparer.",
                    },
                    "donnees": {
                        "type": "object",
                        "description": (
                            "Les données pour remplir le document. "
                            "Facture/devis : numero, date, client_nom, client_adresse, "
                            "prestations (liste de {description, quantite, prix_unitaire}), "
                            "conditions, validite_jours. "
                            "Les champs émetteur sont auto-remplis depuis le profil. "
                            "Confirmation : reference, date, client_nom, details. "
                            "Administratif : titre, destinataire, corps."
                        ),
                    },
                },
                "required": ["type", "donnees"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "confirmer_document",
            "description": (
                "Confirmer et sauvegarder un brouillon de document précédemment "
                "préparé avec preparer_document(). Nécessite le draft_id retourné."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "draft_id": {
                        "type": "string",
                        "description": "L'identifiant du brouillon à confirmer.",
                    },
                },
                "required": ["draft_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lister_documents",
            "description": "Lister les documents déjà générés et sauvegardés.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    # --- Calendrier ---
    {
        "type": "function",
        "function": {
            "name": "lister_echeances",
            "description": (
                "Lister les prochaines échéances fiscales, sociales "
                "et personnalisées du calendrier."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "jours": {
                        "type": "integer",
                        "description": (
                            "Horizon en jours pour les échéances à afficher. Par défaut 30 jours."
                        ),
                        "default": 30,
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ajouter_echeance",
            "description": "Ajouter une nouvelle échéance au calendrier.",
            "parameters": {
                "type": "object",
                "properties": {
                    "titre": {
                        "type": "string",
                        "description": "Titre de l'échéance.",
                    },
                    "date": {
                        "type": "string",
                        "description": "Date de l'échéance au format YYYY-MM-DD.",
                    },
                    "description": {
                        "type": "string",
                        "description": "Description détaillée (optionnel).",
                        "default": "",
                    },
                    "type_echeance": {
                        "type": "string",
                        "enum": ["fiscal", "social", "custom"],
                        "description": "Type d'échéance.",
                        "default": "custom",
                    },
                },
                "required": ["titre", "date"],
            },
        },
    },
    # --- Email ---
    {
        "type": "function",
        "function": {
            "name": "envoyer_email",
            "description": (
                "Envoyer un email via Gmail. "
                "Nécessite que les identifiants Gmail soient configurés."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "destinataire": {
                        "type": "string",
                        "description": "Adresse email du destinataire.",
                    },
                    "objet": {
                        "type": "string",
                        "description": "Objet de l'email.",
                    },
                    "corps": {
                        "type": "string",
                        "description": "Corps de l'email en texte brut.",
                    },
                },
                "required": ["destinataire", "objet", "corps"],
            },
        },
    },
    # --- Mémoire ---
    {
        "type": "function",
        "function": {
            "name": "memoriser",
            "description": (
                "Mémoriser un fait important pour les sessions futures. "
                "Utiliser quand l'utilisateur partage une information clé "
                "(préférences, données métier, décisions, etc.)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "categorie": {
                        "type": "string",
                        "description": (
                            "Catégorie du fait (ex: 'preferences', 'comptabilite', "
                            "'clients', 'activite', 'fiscal', 'social')."
                        ),
                    },
                    "cle": {
                        "type": "string",
                        "description": "Identifiant court du fait (ex: 'taux_tva', 'client_principal').",
                    },
                    "valeur": {
                        "type": "string",
                        "description": "La valeur ou information à mémoriser.",
                    },
                },
                "required": ["categorie", "cle", "valeur"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rappeler",
            "description": (
                "Rechercher dans la mémoire des faits précédemment mémorisés. "
                "Utiliser quand on a besoin d'une info passée."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "categorie": {
                        "type": "string",
                        "description": (
                            "Catégorie dans laquelle chercher (optionnel). "
                            "Si omis, cherche dans toutes les catégories."
                        ),
                    },
                    "query": {
                        "type": "string",
                        "description": "Terme de recherche (cherche dans clé et valeur).",
                        "default": "",
                    },
                },
            },
        },
    },
    # --- Profil ---
    {
        "type": "function",
        "function": {
            "name": "consulter_profil",
            "description": "Consulter le profil de l'utilisateur (informations personnelles et entreprise).",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "modifier_profil",
            "description": (
                "Modifier un ou plusieurs champs du profil utilisateur. "
                "Appelle cet outil IMMÉDIATEMENT quand l'utilisateur donne "
                "des informations personnelles ou d'entreprise."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nom": {"type": "string", "description": "Nom de famille"},
                    "prenom": {"type": "string", "description": "Prénom"},
                    "nom_entreprise": {"type": "string", "description": "Nom de l'entreprise"},
                    "siret": {"type": "string", "description": "Numéro SIRET (14 chiffres)"},
                    "adresse": {"type": "string", "description": "Adresse postale"},
                    "code_postal": {"type": "string", "description": "Code postal"},
                    "ville": {"type": "string", "description": "Ville"},
                    "email": {"type": "string", "description": "Adresse email"},
                    "telephone": {"type": "string", "description": "Numéro de téléphone"},
                    "activite": {"type": "string", "description": "Activité exercée"},
                    "regime_fiscal": {
                        "type": "string",
                        "description": "Régime fiscal (ex: micro-BNC, micro-BIC)",
                    },
                    "regime_social": {"type": "string", "description": "Régime social"},
                    "date_creation_entreprise": {
                        "type": "string",
                        "description": "Date de création (YYYY-MM-DD)",
                    },
                },
            },
        },
    },
]
