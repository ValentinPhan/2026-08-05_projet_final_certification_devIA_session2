"""Import des jeux de donnees consolides (S2) dans la base PostgreSQL (C4).

Prerequis : la base est demarree et le schema applique (voir
`data-pipeline/db/schema.sql`, applique automatiquement au premier demarrage
de `docker-compose up postgres` via `docker-entrypoint-initdb.d`), et les
scripts d'extraction/agregation de S2 ont ete executes (voir
`docs/02-bloc1-data/`).

Portee assumee : ce script importe les donnees issues de la collecte
(produits, recettes, table Ciqual) et le referentiel des allergenes. Il
n'importe PAS de comptes utilisateurs ni d'analyses : ces donnees sont
creees par l'application elle-meme (Bloc 3), pas collectees.

Choix de conception : les ingredients de recette sont importes tels quels
(texte brut scrape, ex. "3 aubergines") sans les relier a un code Ciqual a
ce stade - ce rapprochement semantique (normaliser "3 aubergines" vers
l'aliment Ciqual "Aubergine, crue") releve de l'extraction de compétences
par IA prevue au Bloc 2, pas d'un import de donnees brutes. La colonne
`ingredient.code_ciqual` reste NULL pour ces lignes et sera enrichie
ulterieurement.

Idempotence : toutes les insertions utilisent `ON CONFLICT ... DO UPDATE/NOTHING`,
le script peut donc etre rejoue sans dupliquer les donnees.

Dependances : psycopg2-binary, python-dotenv (voir requirements.txt).

Usage :
    py -m load.import_data
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

from psycopg2.extensions import connection as PgConnection

from common.db import get_connection
from common.io_utils import DATA_DIR, setup_logger

logger = setup_logger("load.import_data")

PROCESSED_DIR = DATA_DIR / "processed"

# Correspondance entre les tags allergenes Open Food Facts et le referentiel
# officiel des 14 allergenes seede dans schema.sql (reglement UE 1169/2011).
OFF_ALLERGEN_TO_REFERENTIEL = {
    "en:gluten": "Gluten (cereales)",
    "en:crustaceans": "Crustaces",
    "en:eggs": "Oeufs",
    "en:fish": "Poissons",
    "en:peanuts": "Arachides",
    "en:soybeans": "Soja",
    "en:milk": "Lait",
    "en:nuts": "Fruits a coque",
    "en:celery": "Celeri",
    "en:mustard": "Moutarde",
    "en:sesame-seeds": "Graines de sesame",
    "en:sulphur-dioxide-and-sulphites": "Anhydride sulfureux et sulfites",
    "en:lupin": "Lupin",
    "en:molluscs": "Mollusques",
}


def _load_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _none_if_nan(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, str) and value.strip().lower() in ("", "nan"):
        return None
    return value


def import_allergen_map(conn: PgConnection) -> dict[str, int]:
    """Charge le referentiel allergene (deja seede par schema.sql) en dictionnaire libelle -> id."""
    with conn.cursor() as cur:
        cur.execute("SELECT id_allergene, libelle FROM allergene")
        return {libelle: id_ for id_, libelle in cur.fetchall()}


def import_ciqual(conn: PgConnection, path: Path) -> int:
    if not path.exists():
        logger.warning("Fichier introuvable, etape ignoree : %s", path)
        return 0
    count = 0
    with path.open(encoding="utf-8") as f, conn.cursor() as cur:
        for row in csv.DictReader(f):
            cur.execute(
                """
                INSERT INTO composition_nutritionnelle
                    (code_ciqual, libelle_aliment, energie_kcal, proteines_g, glucides_g, lipides_g)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (code_ciqual) DO UPDATE SET
                    libelle_aliment = EXCLUDED.libelle_aliment,
                    energie_kcal = EXCLUDED.energie_kcal,
                    proteines_g = EXCLUDED.proteines_g,
                    glucides_g = EXCLUDED.glucides_g,
                    lipides_g = EXCLUDED.lipides_g
                """,
                (
                    row["code_ciqual"],
                    row["libelle_aliment"],
                    _none_if_nan(row.get("energie_kcal")),
                    _none_if_nan(row.get("proteines_g")),
                    _none_if_nan(row.get("glucides_g")),
                    _none_if_nan(row.get("lipides_g")),
                ),
            )
            count += 1
    conn.commit()
    logger.info("Ciqual : %d ligne(s) importee(s)/mise(s) a jour", count)
    return count


def import_produits(conn: PgConnection, path: Path, allergen_map: dict[str, int]) -> int:
    if not path.exists():
        logger.warning("Fichier introuvable, etape ignoree : %s", path)
        return 0
    produits = _load_json(path)
    unmapped_tags: set[str] = set()
    with conn.cursor() as cur:
        for produit in produits:
            cur.execute(
                """
                INSERT INTO produit (code_barres, nom, marque, categorie, nutri_score, ingredients_texte)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (code_barres) DO UPDATE SET
                    nom = EXCLUDED.nom,
                    marque = EXCLUDED.marque,
                    categorie = EXCLUDED.categorie,
                    nutri_score = EXCLUDED.nutri_score,
                    ingredients_texte = EXCLUDED.ingredients_texte
                """,
                (
                    produit["code_barres"],
                    produit["nom"],
                    produit.get("marque") or None,
                    produit.get("categorie") or None,
                    produit.get("nutri_score"),
                    produit["ingredients_texte"],
                ),
            )
            cur.execute("DELETE FROM produit_allergene WHERE code_barres = %s", (produit["code_barres"],))
            for tag in produit.get("allergenes_off", []):
                libelle = OFF_ALLERGEN_TO_REFERENTIEL.get(tag)
                if libelle is None:
                    unmapped_tags.add(tag)
                    continue
                cur.execute(
                    "INSERT INTO produit_allergene (code_barres, id_allergene) VALUES (%s, %s) "
                    "ON CONFLICT DO NOTHING",
                    (produit["code_barres"], allergen_map[libelle]),
                )
    conn.commit()
    if unmapped_tags:
        logger.warning("Tags allergenes Open Food Facts non reconnus (ignores) : %s", sorted(unmapped_tags))
    logger.info("Produits : %d importe(s)/mis a jour", len(produits))
    return len(produits)


def import_recettes(conn: PgConnection, path: Path) -> int:
    if not path.exists():
        logger.warning("Fichier introuvable, etape ignoree : %s", path)
        return 0
    recettes = _load_json(path)
    with conn.cursor() as cur:
        for recette in recettes:
            cur.execute(
                """
                INSERT INTO recette (titre, source_url, instructions)
                VALUES (%s, %s, %s)
                ON CONFLICT (source_url) DO UPDATE SET
                    titre = EXCLUDED.titre,
                    instructions = EXCLUDED.instructions
                RETURNING id_recette
                """,
                (recette["titre"], recette["source_url"], "\n".join(recette.get("instructions", []))),
            )
            id_recette = cur.fetchone()[0]
            cur.execute("DELETE FROM recette_ingredient WHERE id_recette = %s", (id_recette,))
            for ingredient_brut in recette.get("ingredients_bruts", []):
                cur.execute(
                    "INSERT INTO ingredient (libelle) VALUES (%s) "
                    "ON CONFLICT (libelle) DO UPDATE SET libelle = EXCLUDED.libelle "
                    "RETURNING id_ingredient",
                    (ingredient_brut,),
                )
                id_ingredient = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO recette_ingredient (id_recette, id_ingredient) VALUES (%s, %s) "
                    "ON CONFLICT DO NOTHING",
                    (id_recette, id_ingredient),
                )
    conn.commit()
    logger.info("Recettes : %d importee(s)/mise(s) a jour", len(recettes))
    return len(recettes)


def run() -> None:
    conn = get_connection()
    try:
        allergen_map = import_allergen_map(conn)
        logger.info("%d allergene(s) de reference charge(s)", len(allergen_map))
        import_ciqual(conn, PROCESSED_DIR / "composition_nutritionnelle.csv")
        import_produits(conn, PROCESSED_DIR / "produits.json", allergen_map)
        import_recettes(conn, PROCESSED_DIR / "recettes.json")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
