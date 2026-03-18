# CONFIRMATION DE COMMANDE

**Référence :** {{ reference }}
**Date :** {{ date }}

---

**Client :**
{{ client_nom }}
{{ client_adresse | default("") }}

---

## Détails de la commande

{{ details }}

---

Nous vous remercions pour votre confiance.

{{ emetteur_nom | default("Votre entreprise") }}
