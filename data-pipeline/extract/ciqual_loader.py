"""Chargement de la table Ciqual (ANSES) : composition nutritionnelle officielle des aliments.

Source : fichier Excel (.xls) publie librement, sans compte ni cle, sur
data.gouv.fr (jeu de donnees "Table de composition nutritionnelle des
aliments Ciqual 2020"). Le fichier est telecharge une premiere fois puis mis
en cache localement (`data/raw/ciqual/ciqual.xls`) pour ne pas re-solliciter
la source a chaque execution.

Dependances : requests, pandas, xlrd (moteur de lecture du format .xls, voir
requirements.txt).

Usage :
    py extract/ciqual_loader.py

Resultat : data-pipeline/data/raw/ciqual/ciqual_composition.csv
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import requests

from common.io_utils import get_data_dir, setup_logger

logger = setup_logger("extract.ciqual_loader")

USER_AGENT = "NutriScanIA-Formation/0.1 (projet pedagogique Simplon DevIA; contact: nutriscan-ia@example.com)"
HEADERS = {"User-Agent": USER_AGENT}

# Ressource "Table Ciqual 2020_FR_2020 07 07.xls" du jeu de donnees data.gouv.fr
# "table-de-composition-nutritionnelle-des-aliments-ciqual-2020".
CIQUAL_URL = "https://www.data.gouv.fr/api/1/datasets/r/bcdb7fec-875c-42aa-ba6e-460adf97aad3"
SHEET_NAME = "compo"
REQUEST_TIMEOUT_SECONDS = 30

# Correspondance colonnes Ciqual (nom officiel, en francais) -> schema NutriScan IA.
COLUMN_MAPPING = {
    "alim_code": "code_ciqual",
    "alim_nom_fr": "libelle_aliment",
    "alim_grp_nom_fr": "groupe_aliment",
    "Energie, Règlement UE N° 1169/2011 (kcal/100 g)": "energie_kcal",
    "Protéines, N x 6.25 (g/100 g)": "proteines_g",
    "Glucides (g/100 g)": "glucides_g",
    "Lipides (g/100 g)": "lipides_g",
}

# Marqueurs Ciqual pour une valeur non mesuree (documentation Ciqual : "-" = non determinee).
MISSING_VALUE_MARKERS = {"-", "", "traces", "tr"}
# Ciqual note "< x" une valeur inferieure au seuil de quantification analytique :
# assimilee ici a une quantite negligeable (0), convention usuelle pour un calcul nutritionnel.
BELOW_QUANTIFICATION_LIMIT = re.compile(r"^<\s*[\d.,]+$")


def _download_if_needed(destination: Path) -> Path:
    if destination.exists():
        logger.info("Fichier Ciqual deja present en cache : %s", destination)
        return destination

    logger.info("Telechargement de la table Ciqual depuis %s", CIQUAL_URL)
    response = requests.get(CIQUAL_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    destination.write_bytes(response.content)
    logger.info("Fichier Ciqual sauvegarde : %s (%d octets)", destination, len(response.content))
    return destination


def _to_float(value: object) -> float | None:
    """Convertit une valeur Ciqual (virgule decimale, marqueurs Ciqual) en float, ou None si absente."""
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in MISSING_VALUE_MARKERS:
        return None
    if BELOW_QUANTIFICATION_LIMIT.match(text):
        return 0.0
    try:
        return float(text.replace(",", "."))
    except ValueError:
        return None


def run() -> Path:
    """Telecharge (si besoin), nettoie et sauvegarde la table de composition nutritionnelle Ciqual."""
    raw_dir = get_data_dir("raw", "ciqual")
    xls_path = _download_if_needed(raw_dir / "ciqual.xls")

    df = pd.read_excel(xls_path, sheet_name=SHEET_NAME, engine="xlrd")
    df = df[list(COLUMN_MAPPING.keys())].rename(columns=COLUMN_MAPPING)

    for column in ("energie_kcal", "proteines_g", "glucides_g", "lipides_g"):
        original_values = df[column]
        converted = original_values.map(_to_float)
        unresolved = original_values[converted.isna() & original_values.notna()]
        unresolved = unresolved[~unresolved.astype(str).str.strip().str.lower().isin(MISSING_VALUE_MARKERS)]
        if len(unresolved) > 0:
            logger.warning(
                "%s : %d valeur(s) non reconnue(s) mises a vide, ex. %r",
                column, len(unresolved), unresolved.iloc[0],
            )
        df[column] = converted

    output_path = raw_dir / "ciqual_composition.csv"
    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("%d aliment(s) Ciqual sauvegarde(s) dans %s", len(df), output_path)
    return output_path


if __name__ == "__main__":
    run()
