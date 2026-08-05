"""Utilitaires partages par les scripts ai-service (chemins de sortie, logging).

Duplique volontairement data-pipeline/common/io_utils.py plutot que de le
partager entre composants : voir docs/01-cadrage/architecture.md, les 3
composants (data-pipeline, ai-service, app) restent independants et ne
communiquent que par API REST, jamais par import de code entre eux.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

AI_SERVICE_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = AI_SERVICE_ROOT / "data"


def get_data_dir(*parts: str) -> Path:
    """Retourne (et cree si besoin) un sous-dossier de ai-service/data/."""
    path = DATA_DIR.joinpath(*parts)
    path.mkdir(parents=True, exist_ok=True)
    return path


def setup_logger(name: str) -> logging.Logger:
    """Configure un logger console commun a tous les scripts ai-service."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
