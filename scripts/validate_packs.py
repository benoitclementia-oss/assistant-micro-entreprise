"""Script de validation des packs de données.

Vérifie la qualité, la couverture et l'intégrité des collections Qdrant
selon les standards professionnels de data quality.

Usage :
    python -m scripts.validate_packs                    # Valider tous les packs
    python -m scripts.validate_packs --pack micro       # Un seul pack
    python -m scripts.validate_packs --verbose           # Détails complets
    python -m scripts.validate_packs --export rapport    # Exporter en JSON
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

from . import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ================================================================
# Définition des packs et de leurs collections
# ================================================================

PACKS = {
    "micro": {
        "nom": "Micro-Entrepreneur Complet",
        "collections": [
            "lois_fiscales",
            "regles_comptables",
            "reglementations_administratives",
            "droit_consommation",
            "securite_sociale_micro",
            "reglements_europeens",
            "guides_cnil_tpe",
        ],
        "min_articles_par_collection": {
            "lois_fiscales": 100,
            "regles_comptables": 50,
            "reglementations_administratives": 20,
            "droit_consommation": 100,
            "securite_sociale_micro": 20,
            "reglements_europeens": 50,
            "guides_cnil_tpe": 10,
        },
        "mots_cles_obligatoires": [
            "micro-entreprise",
            "chiffre d'affaires",
            "TVA",
            "cotisations",
            "facture",
            "URSSAF",
            "SIRET",
        ],
    },
    "artisanat": {
        "nom": "Artisanat Réglementé",
        "collections": [
            "artisanat_reglemente",
        ],
        "min_articles_par_collection": {
            "artisanat_reglemente": 30,
        },
        "mots_cles_obligatoires": [
            "artisan",
            "qualification",
            "répertoire des métiers",
            "chambre de métiers",
        ],
    },
    "haccp": {
        "nom": "HACCP & Hygiène Alimentaire",
        "collections": [
            "hygiene_alimentaire",
        ],
        "min_articles_par_collection": {
            "hygiene_alimentaire": 50,
        },
        "mots_cles_obligatoires": [
            "hygiène",
            "alimentaire",
            "HACCP",
            "traçabilité",
            "denrées",
        ],
    },
    "pmr": {
        "nom": "Accessibilité PMR",
        "collections": [
            "accessibilite_pmr",
        ],
        "min_articles_par_collection": {
            "accessibilite_pmr": 20,
        },
        "mots_cles_obligatoires": [
            "accessibilité",
            "handicap",
            "établissement recevant du public",
        ],
    },
}


# ================================================================
# Tests de validation
# ================================================================


def check_collection_exists(client: QdrantClient, name: str) -> dict:
    """Vérifier qu'une collection existe dans Qdrant."""
    try:
        info = client.get_collection(name)
        return {
            "test": f"Collection '{name}' existe",
            "status": "PASS",
            "details": {
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "status": info.status.value if info.status else "unknown",
            },
        }
    except (UnexpectedResponse, Exception) as e:
        return {
            "test": f"Collection '{name}' existe",
            "status": "FAIL",
            "details": {"error": str(e)},
        }


def check_min_articles(client: QdrantClient, name: str, minimum: int) -> dict:
    """Vérifier le nombre minimum d'articles/points."""
    try:
        info = client.get_collection(name)
        count = info.points_count or 0
        passed = count >= minimum
        return {
            "test": f"'{name}' >= {minimum} points",
            "status": "PASS" if passed else "FAIL",
            "details": {"actual": count, "minimum": minimum},
        }
    except Exception as e:
        return {
            "test": f"'{name}' >= {minimum} points",
            "status": "FAIL",
            "details": {"error": str(e)},
        }


def check_vector_dimension(client: QdrantClient, name: str) -> dict:
    """Vérifier que la dimension des vecteurs est correcte (1536)."""
    try:
        info = client.get_collection(name)
        vec_config = info.config.params.vectors
        # vec_config peut être un dict ou un VectorParams
        if hasattr(vec_config, "size"):
            dim = vec_config.size
        elif isinstance(vec_config, dict):
            dim = vec_config.get("size", 0)
        else:
            dim = 0
        passed = dim == config.EMBEDDING_DIM
        return {
            "test": f"'{name}' dimension == {config.EMBEDDING_DIM}",
            "status": "PASS" if passed else "FAIL",
            "details": {"actual": dim, "expected": config.EMBEDDING_DIM},
        }
    except Exception as e:
        return {
            "test": f"'{name}' dimension vecteurs",
            "status": "FAIL",
            "details": {"error": str(e)},
        }


def check_keyword_coverage(client: QdrantClient, name: str, keywords: list[str]) -> dict:
    """Vérifier que les mots-clés obligatoires sont présents dans la collection.

    Utilise une recherche par scroll avec filtre textuel.
    """
    found = []
    missing = []
    try:
        for kw in keywords:
            # Récupérer quelques points et chercher le mot-clé dans les payloads
            results, _ = client.scroll(
                collection_name=name,
                limit=100,
                with_payload=True,
            )
            kw_found = False
            for point in results:
                payload = point.payload or {}
                text = " ".join(str(v) for v in payload.values()).lower()
                if kw.lower() in text:
                    kw_found = True
                    break
            if kw_found:
                found.append(kw)
            else:
                missing.append(kw)
    except Exception as e:
        return {
            "test": f"'{name}' mots-clés obligatoires",
            "status": "FAIL",
            "details": {"error": str(e)},
        }

    passed = len(missing) == 0
    return {
        "test": f"'{name}' mots-clés ({len(found)}/{len(keywords)})",
        "status": "PASS" if passed else "WARN",
        "details": {"found": found, "missing": missing},
    }


def check_no_empty_vectors(client: QdrantClient, name: str) -> dict:
    """Vérifier qu'il n'y a pas de vecteurs vides (tous zéros)."""
    try:
        results, _ = client.scroll(
            collection_name=name,
            limit=50,
            with_vectors=True,
        )
        empty_count = 0
        for point in results:
            vec = point.vector
            if vec and all(v == 0.0 for v in vec):
                empty_count += 1
        passed = empty_count == 0
        return {
            "test": f"'{name}' pas de vecteurs vides",
            "status": "PASS" if passed else "FAIL",
            "details": {
                "checked": len(results),
                "empty_vectors": empty_count,
            },
        }
    except Exception as e:
        return {
            "test": f"'{name}' vecteurs vides",
            "status": "FAIL",
            "details": {"error": str(e)},
        }


def check_metadata_completeness(client: QdrantClient, name: str) -> dict:
    """Vérifier que les métadonnées essentielles sont présentes."""
    required_fields = ["titre", "texte", "code_source", "article_id"]
    try:
        results, _ = client.scroll(
            collection_name=name,
            limit=50,
            with_payload=True,
        )
        issues = []
        for point in results:
            payload = point.payload or {}
            for field in required_fields:
                if field not in payload or not payload[field]:
                    issues.append(f"Point {point.id} : champ '{field}' manquant ou vide")
        passed = len(issues) == 0
        return {
            "test": f"'{name}' métadonnées complètes",
            "status": "PASS" if passed else "WARN",
            "details": {
                "checked": len(results),
                "issues_count": len(issues),
                "sample_issues": issues[:5],
            },
        }
    except Exception as e:
        return {
            "test": f"'{name}' métadonnées",
            "status": "FAIL",
            "details": {"error": str(e)},
        }


# ================================================================
# Orchestration
# ================================================================


def validate_pack(client: QdrantClient, pack_id: str, verbose: bool = False) -> dict:
    """Valider un pack complet."""
    pack = PACKS[pack_id]
    logger.info("=== Validation du pack '%s' (%s) ===", pack_id, pack["nom"])

    results = []
    for coll_name in pack["collections"]:
        # 1. Existence
        results.append(check_collection_exists(client, coll_name))

        # Si la collection n'existe pas, on passe les tests suivants
        if results[-1]["status"] == "FAIL":
            logger.warning("  Collection '%s' absente — tests suivants ignorés", coll_name)
            continue

        # 2. Nombre minimum de points
        min_articles = pack["min_articles_par_collection"].get(coll_name, 10)
        results.append(check_min_articles(client, coll_name, min_articles))

        # 3. Dimension vecteurs
        results.append(check_vector_dimension(client, coll_name))

        # 4. Pas de vecteurs vides
        results.append(check_no_empty_vectors(client, coll_name))

        # 5. Métadonnées complètes
        results.append(check_metadata_completeness(client, coll_name))

    # 6. Couverture mots-clés (sur la première collection du pack)
    primary_coll = pack["collections"][0]
    try:
        client.get_collection(primary_coll)
        results.append(check_keyword_coverage(client, primary_coll, pack["mots_cles_obligatoires"]))
    except Exception:
        pass

    # Résumé
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    warn_count = sum(1 for r in results if r["status"] == "WARN")
    fail_count = sum(1 for r in results if r["status"] == "FAIL")

    summary = {
        "pack_id": pack_id,
        "pack_nom": pack["nom"],
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(results),
        "pass": pass_count,
        "warn": warn_count,
        "fail": fail_count,
        "verdict": "PASS" if fail_count == 0 else "FAIL",
        "tests": results,
    }

    # Affichage
    for r in results:
        icon = {"PASS": "OK", "WARN": "!!", "FAIL": "XX"}[r["status"]]
        logger.info("  [%s] %s", icon, r["test"])
        if verbose and r.get("details"):
            for k, v in r["details"].items():
                logger.info("       %s: %s", k, v)

    logger.info(
        "  Résultat : %d PASS / %d WARN / %d FAIL → %s",
        pass_count,
        warn_count,
        fail_count,
        summary["verdict"],
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Validation des packs de données")
    parser.add_argument(
        "--pack",
        choices=list(PACKS.keys()),
        help="Pack à valider (défaut : tous)",
    )
    parser.add_argument("--verbose", action="store_true", help="Détails complets")
    parser.add_argument("--export", help="Exporter le rapport en JSON (chemin du fichier)")
    args = parser.parse_args()

    client = QdrantClient(url=config.QDRANT_URL)

    packs_to_validate = [args.pack] if args.pack else list(PACKS.keys())
    all_results = []

    for pack_id in packs_to_validate:
        result = validate_pack(client, pack_id, verbose=args.verbose)
        all_results.append(result)

    # Résumé global
    total_pass = sum(r["pass"] for r in all_results)
    total_fail = sum(r["fail"] for r in all_results)
    total_warn = sum(r["warn"] for r in all_results)
    global_verdict = "PASS" if total_fail == 0 else "FAIL"

    logger.info("")
    logger.info("=== RÉSUMÉ GLOBAL ===")
    logger.info("  Packs validés : %d", len(all_results))
    logger.info("  Tests : %d PASS / %d WARN / %d FAIL", total_pass, total_warn, total_fail)
    logger.info("  Verdict global : %s", global_verdict)

    if args.export:
        export_path = Path(args.export)
        report = {
            "generated_at": datetime.now().isoformat(),
            "verdict": global_verdict,
            "packs": all_results,
        }
        export_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("  Rapport exporté : %s", export_path)

    sys.exit(0 if global_verdict == "PASS" else 1)


if __name__ == "__main__":
    main()
