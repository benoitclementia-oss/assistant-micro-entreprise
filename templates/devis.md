# DEVIS N° {{ numero }}

**Date :** {{ date }}
**Validité :** {{ validite_jours | default(30) }} jours

---

**Émetteur :**
{{ emetteur_nom | default("Votre entreprise") }}
{{ emetteur_adresse | default("") }}
SIRET : {{ emetteur_siret | default("À compléter") }}

**Client :**
{{ client_nom }}
{{ client_adresse | default("") }}

---

## Prestations proposées

| Description | Quantité | Prix unitaire (€) | Total (€) |
|---|---|---|---|
{% for p in prestations -%}
| {{ p.description }} | {{ p.quantite }} | {{ "%.2f" | format(p.prix_unitaire) }} | {{ "%.2f" | format(p.quantite * p.prix_unitaire) }} |
{% endfor -%}

---

**Total : {{ "%.2f" | format(total) }} €**

---

*TVA non applicable, article 293 B du Code général des impôts.*

{{ conditions | default("") }}

**Bon pour accord :**

Date :                          Signature :
