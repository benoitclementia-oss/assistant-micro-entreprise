# FACTURE N° {{ numero | default("À compléter") }}

**Date :** {{ date | default("À compléter") }}

---

**Émetteur :**
{{ emetteur_nom | default("Votre entreprise") }}
{{ emetteur_adresse | default("") }}
SIRET : {{ emetteur_siret | default("À compléter") }}

**Client :**
{{ client_nom | default("À compléter") }}
{{ client_adresse | default("") }}

---

## Prestations

| Description | Quantité | Prix unitaire (€) | Total (€) |
|---|---|---|---|
{% for p in prestations | default([]) -%}
| {{ p.description }} | {{ p.quantite }} | {{ "%.2f" | format(p.prix_unitaire) }} | {{ "%.2f" | format(p.quantite * p.prix_unitaire) }} |
{% endfor -%}

---

{% set computed_total = namespace(val=0) -%}
{% for p in prestations | default([]) -%}
{% set computed_total.val = computed_total.val + p.quantite * p.prix_unitaire -%}
{% endfor -%}
**Total : {{ "%.2f" | format(total | default(computed_total.val)) }} €**

---

*TVA non applicable, article 293 B du Code général des impôts.*

Conditions de paiement : {{ conditions | default("Paiement à réception de la facture.") }}
