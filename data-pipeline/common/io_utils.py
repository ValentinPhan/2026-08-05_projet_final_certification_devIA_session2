"""Utilitaires partages par les scripts data-pipeline (chemins de sortie, logging)."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

DATA_PIPELINE_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = DATA_PIPELINE_ROOT / "data"


def get_data_dir(*parts: str) -> Path:
    """Retourne (et cree si besoin) un sous-dossier de data-pipeline/data/."""
    path = DATA_DIR.joinpath(*parts)
    path.mkdir(parents=True, exist_ok=True)
    return path


def setup_logger(name: str) -> logging.Logger:
    """Configure un logger console commun a tous les scripts d'extraction/transformation."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
