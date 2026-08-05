"""Requete analytique sur l'export complet Open Food Facts via DuckDB (competence "systeme big data").

Open Food Facts publie un export complet de sa base (plusieurs millions de
produits, plusieurs Go). Ce volume depasse ce qu'on voudrait charger en
memoire ou dupliquer dans la base applicative : c'est le cas d'usage type
d'un moteur analytique "big data" comme DuckDB, capable d'interroger le
fichier distant directement via HTTP (extension `httpfs`), en flux, sans le
telecharger integralement au prealable.

Aucune cle ni compte n'est necessaire : le fichier est un export public.

Choix techniques :
- Le fichier CSV compresse (`en.openfoodfacts.org.products.csv.gz`, ~1,3 Go
  compresse / ~9 Go decompresse, 4,65 millions de lignes) est prefere a
  l'export Parquet miroir sur Hugging Face : DuckDB le lit en flux sequentiel
  (rapide et fiable ici), alors que le Parquet distant multiplie les petites
  requetes HTTP pour ses metadonnees, ce qui s'est revele tres lent depuis
  cet environnement reseau.
- La requete est bornee par `LIMIT ECHANTILLON_LIGNES` sur le flux pour que
  le script reste reproductible en quelques secondes. Retirer ce LIMIT
  execute exactement la meme requete sur l'integralite du fichier distant
  (memes colonnes, meme logique), au prix d'un temps d'execution beaucoup
  plus long : ce compromis (echantillon representatif vs scan complet) est
  assume et documente ici plutot que cache.

Dependances : duckdb (voir requirements.txt). Necessite un acces reseau
sortant (l'extension `httpfs` est installee automatiquement au premier
lancement).

Usage :
    py extract/duckdb_openfoodfacts.py

Resultat : data-pipeline/data/raw/duckdb/nutriscore_par_pays.csv
"""
from __future__ import annotations

import time
from pathlib import Path

import duckdb

from common.io_utils import get_data_dir, setup_logger

logger = setup_logger("extract.duckdb_openfoodfacts")

EXPORT_URL = "https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz"
ECHANTILLON_LIGNES = 500_000
PAYS_ANALYSE = "France"

QUERY = f"""
WITH echantillon AS (
    SELECT code, countries_en, nutriscore_grade
    FROM read_csv('{EXPORT_URL}', delim='\t', header=true, sample_size=5000, ignore_errors=true)
    LIMIT {ECHANTILLON_LIGNES}
)
SELECT nutriscore_grade, COUNT(*) AS nb_produits
FROM echantillon
WHERE countries_en ILIKE '%{PAYS_ANALYSE}%'
  AND nutriscore_grade IS NOT NULL
  AND nutriscore_grade NOT IN ('', 'unknown', 'not-applicable')
GROUP BY nutriscore_grade
ORDER BY nutriscore_grade
"""


def run() -> Path:
    """Interroge l'export distant Open Food Facts et sauvegarde la distribution des Nutri-Score."""
    output_dir = get_data_dir("raw", "duckdb")
    con = duckdb.connect()
    con.execute("INSTALL httpfs;")
    con.execute("LOAD httpfs;")
    con.execute("SET enable_progress_bar=false;")

    logger.info(
        "Requete sur les %d premieres lignes de l'export distant (%s)",
        ECHANTILLON_LIGNES, EXPORT_URL,
    )
    start = time.time()
    try:
        rows = con.execute(QUERY).fetchall()
    except duckdb.Error as exc:
        logger.error("Echec de la requete DuckDB sur l'export distant : %s", exc)
        raise
    elapsed = time.time() - start
    logger.info("Requete terminee en %.1fs (%d ligne(s) de resultat)", elapsed, len(rows))

    output_path = output_dir / "nutriscore_par_pays.csv"
    with output_path.open("w", encoding="utf-8") as f:
        f.write("nutriscore_grade,nb_produits\n")
        for grade, count in rows:
            f.write(f"{grade},{count}\n")
            logger.info("Nutri-Score %s : %d produit(s)", grade, count)

    logger.info("Resultat sauvegarde dans %s", output_path)
    return output_path


if __name__ == "__main__":
    run()
