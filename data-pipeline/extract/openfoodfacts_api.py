"""Extraction de produits alimentaires depuis l'API ouverte Open Food Facts.

Aucune cle API ni compte n'est necessaire : l'API est publique. Deux
endpoints sont combines car ils ont des roles complementaires :

1. https://search.openfoodfacts.org/search
   decouverte de codes-barres pertinents a partir d'une recherche plein
   texte par terme alimentaire (le nouvel index "Search-a-licious").
2. https://world.openfoodfacts.org/api/v2/product/<code>.json
   fiche produit complete (ingredients, allergenes, valeurs nutritionnelles) ;
   c'est l'endpoint le plus stable et le plus documente d'Open Food Facts,
   utilise ici pour la recuperation detaillee.

Dependances : requests (voir requirements.txt).

Usage :
    py extract/openfoodfacts_api.py

Resultat : data-pipeline/data/raw/openfoodfacts/openfoodfacts_products.json
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import requests

from common.io_utils import get_data_dir, setup_logger

logger = setup_logger("extract.openfoodfacts_api")

USER_AGENT = "NutriScanIA-Formation/0.1 (projet pedagogique Simplon DevIA; contact: nutriscan-ia@example.com)"
HEADERS = {"User-Agent": USER_AGENT}

SEARCH_URL = "https://search.openfoodfacts.org/search"
PRODUCT_URL = "https://world.openfoodfacts.org/api/v2/product/{code}.json"

# Termes couvrant des categories variees (donc des profils d'allergenes
# varies) pour constituer un jeu de donnees representatif du cas d'usage.
SEARCH_TERMS = [
    "biscuit",
    "yaourt",
    "pain",
    "chocolat",
    "pizza",
    "houmous",
    "lait",
    "jus de fruit",
]
PRODUCTS_PER_TERM = 6
REQUEST_DELAY_SECONDS = 1.2
REQUEST_TIMEOUT_SECONDS = 15
MAX_RETRIES = 3

PRODUCT_FIELDS = [
    "code",
    "product_name",
    "brands",
    "categories_tags",
    "ingredients_text",
    "ingredients_text_fr",
    "allergens_tags",
    "nutriscore_grade",
    "nutriments",
]


def _get_with_retry(url: str, params: dict[str, Any]) -> requests.Response | None:
    """Effectue un GET avec repli en cas de limitation de debit (429) ou d'erreur serveur (5xx).

    Open Food Facts applique une limitation de debit sur ses API publiques :
    en cas de reponse 429, on attend la duree indiquee par l'en-tete
    `Retry-After` (a defaut, un delai croissant) avant de reessayer.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        except requests.RequestException as exc:
            logger.warning("Erreur reseau (tentative %d/%d) sur %s : %s", attempt, MAX_RETRIES, url, exc)
            time.sleep(attempt * REQUEST_DELAY_SECONDS)
            continue

        if response.status_code == 429 or response.status_code >= 500:
            wait = int(response.headers.get("Retry-After", attempt * 2))
            logger.warning(
                "Reponse %d sur %s (tentative %d/%d) : nouvelle tentative dans %ds",
                response.status_code, url, attempt, MAX_RETRIES, wait,
            )
            time.sleep(wait)
            continue

        return response

    logger.warning("Abandon apres %d tentatives sur %s", MAX_RETRIES, url)
    return None


def discover_product_codes(term: str, limit: int) -> list[str]:
    """Interroge l'API de recherche pour obtenir des codes-barres candidats pour un terme donne."""
    params = {"q": term, "page_size": limit, "fields": "code"}
    response = _get_with_retry(SEARCH_URL, params)
    if response is None or not response.ok:
        logger.warning("Echec de la recherche pour '%s'", term)
        return []
    hits = response.json().get("hits", [])
    codes = [hit["code"] for hit in hits if hit.get("code")]
    logger.info("Terme '%s' : %d code(s) trouve(s)", term, len(codes))
    return codes


def fetch_product(code: str) -> dict[str, Any] | None:
    """Recupere la fiche complete d'un produit par son code-barres, ou None si indisponible."""
    url = PRODUCT_URL.format(code=code)
    params = {"fields": ",".join(PRODUCT_FIELDS)}
    response = _get_with_retry(url, params)
    if response is None:
        return None
    if response.status_code == 404:
        logger.warning("Produit %s introuvable (404) sur Open Food Facts", code)
        return None
    if not response.ok:
        logger.warning("Reponse inattendue (%d) pour le produit %s", response.status_code, code)
        return None

    payload = response.json()
    if payload.get("status") != 1:
        logger.warning("Produit %s introuvable sur Open Food Facts", code)
        return None
    return payload["product"]


def run() -> Path:
    """Decouvre puis recupere un jeu de produits Open Food Facts, et sauvegarde le resultat brut."""
    raw_dir = get_data_dir("raw", "openfoodfacts")
    all_codes: set[str] = set()

    for term in SEARCH_TERMS:
        try:
            codes = discover_product_codes(term, PRODUCTS_PER_TERM)
        except requests.RequestException as exc:
            logger.warning("Echec de la recherche pour '%s' : %s", term, exc)
            continue
        all_codes.update(codes)
        time.sleep(REQUEST_DELAY_SECONDS)

    logger.info("%d code(s) unique(s) a recuperer en detail", len(all_codes))

    products: list[dict[str, Any]] = []
    for code in sorted(all_codes):
        product = fetch_product(code)
        if product is not None:
            products.append(product)
        time.sleep(REQUEST_DELAY_SECONDS)

    output_path = raw_dir / "openfoodfacts_products.json"
    output_path.write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("%d produit(s) sauvegarde(s) dans %s", len(products), output_path)
    return output_path


if __name__ == "__main__":
    run()
