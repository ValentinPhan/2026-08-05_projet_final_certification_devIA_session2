"""Agregation et nettoyage des donnees collectees (Open Food Facts, recettes, Ciqual).

Ce script consolide les trois sources extraites dans `extract/` en jeux de
donnees prets a etre importes en base (voir `data-pipeline/db/`, S3) :
suppression des entrees corrompues (donnees essentielles manquantes),
homogeneisation des formats (texte, nombres, dates) et deduplication.

Prerequis : avoir execute au prealable
    py extract/openfoodfacts_api.py
    py extract/scrape_recettes.py
    py extract/ciqual_loader.py

Dependances : pandas (voir requirements.txt).

Usage :
    py transform/clean_aggregate.py

Resultat :
    data-pipeline/data/processed/produits.json
    data-pipeline/data/processed/recettes.json
    data-pipeline/data/processed/composition_nutritionnelle.csv
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from common.io_utils import DATA_DIR, get_data_dir, setup_logger

logger = setup_logger("transform.clean_aggregate")

RAW_DIR = DATA_DIR / "raw"


def _clean_text(value: Any) -> str:
    """Supprime les espaces superflus et harmonise une valeur textuelle."""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _first_category(categories_tags: list[str] | None) -> str:
    """Extrait une categorie lisible a partir du premier tag Open Food Facts (ex. 'en:biscuits' -> 'biscuits')."""
    if not categories_tags:
        return ""
    tag = categories_tags[0]
    return tag.split(":", 1)[-1].replace("-", " ")


def _nutriment_100g(nutriments: dict[str, Any] | None, cle: str) -> float | None:
    """Lit une valeur pour 100g/100ml dans le sous-objet `nutriments` d'Open Food Facts.

    Champ deja recupere par extract/openfoodfacts_api.py (voir PRODUCT_FIELDS)
    mais jusqu'ici jamais persiste au-dela de l'extraction brute - necessaire
    au score nutritionnel detaille (US6, S9), au-dela du seul Nutri-Score.
    """
    if not nutriments:
        return None
    valeur = nutriments.get(f"{cle}_100g")
    if valeur is None or not isinstance(valeur, (int, float)):
        return None
    return float(valeur)


def clean_produits(raw_products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Nettoie les produits Open Food Facts : entrees corrompues supprimees, champs homogeneises."""
    seen_codes: set[str] = set()
    cleaned: list[dict[str, Any]] = []
    dropped_no_code = 0
    dropped_incomplete = 0
    dropped_duplicate = 0

    for product in raw_products:
        code = _clean_text(product.get("code"))
        if not code:
            dropped_no_code += 1
            continue
        if code in seen_codes:
            dropped_duplicate += 1
            continue

        name = _clean_text(product.get("product_name"))
        ingredients = _clean_text(product.get("ingredients_text_fr")) or _clean_text(product.get("ingredients_text"))
        if not name or not ingredients:
            # Un produit sans nom ou sans texte d'ingredients est inexploitable
            # pour l'analyse de compatibilite allergene : entree consideree corrompue.
            dropped_incomplete += 1
            continue

        seen_codes.add(code)
        nutriscore = _clean_text(product.get("nutriscore_grade")).lower()
        nutriments = product.get("nutriments")
        cleaned.append({
            "code_barres": code,
            "nom": name,
            "marque": _clean_text(product.get("brands")),
            "categorie": _first_category(product.get("categories_tags")),
            "nutri_score": nutriscore if nutriscore and nutriscore != "unknown" else None,
            "ingredients_texte": ingredients,
            "allergenes_off": product.get("allergens_tags") or [],
            "energie_kcal_100g": _nutriment_100g(nutriments, "energy-kcal"),
            "proteines_g_100g": _nutriment_100g(nutriments, "proteins"),
            "glucides_g_100g": _nutriment_100g(nutriments, "carbohydrates"),
            "lipides_g_100g": _nutriment_100g(nutriments, "fat"),
        })

    logger.info(
        "Produits : %d conserve(s), %d sans code, %d incomplet(s), %d doublon(s)",
        len(cleaned), dropped_no_code, dropped_incomplete, dropped_duplicate,
    )
    return cleaned


def clean_recettes(raw_recipes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Nettoie les recettes scrapees : titre normalise, ingredients homogeneises."""
    cleaned: list[dict[str, Any]] = []
    dropped_no_ingredients = 0
    incomplete_instructions = 0

    for recipe in raw_recipes:
        ingredients = [
            re.sub(r"\s*,\s*$", "", _clean_text(item))
            for item in recipe.get("ingredients_bruts", [])
            if _clean_text(item)
        ]
        if not ingredients:
            dropped_no_ingredients += 1
            continue

        titre = _clean_text(recipe.get("titre"))
        titre = re.sub(r"^Livre de cuisine\s*/\s*", "", titre)

        instructions = [_clean_text(step) for step in recipe.get("instructions", []) if _clean_text(step)]
        if not instructions:
            # Recette conservee (les ingredients suffisent pour l'analyse de
            # compatibilite allergene), mais la lacune est tracee pour le
            # rapport qualite plutot que masquee.
            incomplete_instructions += 1

        cleaned.append({
            "titre": titre,
            "source_url": recipe.get("source_url", ""),
            "ingredients_bruts": ingredients,
            "instructions": instructions,
        })

    logger.info(
        "Recettes : %d conservee(s), %d sans ingredient exploitable, %d sans instructions (conservees quand meme)",
        len(cleaned), dropped_no_ingredients, incomplete_instructions,
    )
    return cleaned


def clean_ciqual(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoie la table Ciqual : entrees corrompues (aucune valeur nutritionnelle exploitable) supprimees."""
    before = len(df)
    df = df.dropna(subset=["libelle_aliment"])
    nutrient_columns = ["energie_kcal", "proteines_g", "glucides_g", "lipides_g"]
    df = df[df[nutrient_columns].notna().any(axis=1)]
    df = df.drop_duplicates(subset=["code_ciqual"])
    logger.info("Ciqual : %d conserve(s) sur %d (entrees sans donnee exploitable supprimees)", len(df), before)
    return df


def run() -> dict[str, Path]:
    """Charge les jeux de donnees bruts, les nettoie, et sauvegarde les jeux de donnees consolides."""
    processed_dir = get_data_dir("processed")
    outputs: dict[str, Path] = {}

    products_path = RAW_DIR / "openfoodfacts" / "openfoodfacts_products.json"
    if products_path.exists():
        raw_products = json.loads(products_path.read_text(encoding="utf-8"))
        produits = clean_produits(raw_products)
        output_path = processed_dir / "produits.json"
        output_path.write_text(json.dumps(produits, ensure_ascii=False, indent=2), encoding="utf-8")
        outputs["produits"] = output_path
    else:
        logger.warning("Fichier introuvable, etape ignoree : %s (executer extract/openfoodfacts_api.py)", products_path)

    recipes_path = RAW_DIR / "recettes" / "recettes.json"
    if recipes_path.exists():
        raw_recipes = json.loads(recipes_path.read_text(encoding="utf-8"))
        recettes = clean_recettes(raw_recipes)
        output_path = processed_dir / "recettes.json"
        output_path.write_text(json.dumps(recettes, ensure_ascii=False, indent=2), encoding="utf-8")
        outputs["recettes"] = output_path
    else:
        logger.warning("Fichier introuvable, etape ignoree : %s (executer extract/scrape_recettes.py)", recipes_path)

    ciqual_path = RAW_DIR / "ciqual" / "ciqual_composition.csv"
    if ciqual_path.exists():
        df = pd.read_csv(ciqual_path)
        df = clean_ciqual(df)
        output_path = processed_dir / "composition_nutritionnelle.csv"
        df.to_csv(output_path, index=False, encoding="utf-8")
        outputs["ciqual"] = output_path
    else:
        logger.warning("Fichier introuvable, etape ignoree : %s (executer extract/ciqual_loader.py)", ciqual_path)

    logger.info("Jeux de donnees consolides disponibles dans %s", processed_dir)
    return outputs


if __name__ == "__main__":
    run()
