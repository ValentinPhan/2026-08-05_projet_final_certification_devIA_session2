"""Journalisation structuree du backend applicatif (competence C20).

Format JSON (une ligne par evenement) plutot que du texte libre : facilite
l'ingestion par un outil d'agregation de logs (ex. Grafana Loki, Elastic)
sans parsing fragile par expression reguliere.

Regle de confidentialite (RGPD, voir docs/rgpd/registre-traitements.md) : ne
journalise jamais de secret (mot de passe, jeton de session) ni de donnee de
sante en clair (libelle d'allergene, niveau) - uniquement des metadonnees
operationnelles (quel type d'evenement, pour quel identifiant utilisateur,
quand). Le detail du profil allergene n'apparait donc dans aucun log.
"""
from __future__ import annotations

import json
import logging
import sys
from typing import Any


class _FormateurJSON(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "niveau": record.levelname,
            "logger": record.name,
        }
        payload.update(getattr(record, "champs", {}))
        return json.dumps(payload, ensure_ascii=False)


def get_logger() -> logging.Logger:
    logger = logging.getLogger("nutriscan.backend")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_FormateurJSON())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def evenement(logger: logging.Logger, nom: str, **champs: Any) -> None:
    """Journalise un evenement structure (ex. nom="connexion_reussie", id_utilisateur=42)."""
    logger.info(nom, extra={"champs": {"evenement": nom, **champs}})
