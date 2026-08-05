"""Agregation de veille technique et reglementaire (Bloc 2, competence C6).

Interroge 4 flux RSS/Atom publics, sans compte ni cle, choisis pour couvrir
a la fois la reglementation mobilisee par NutriScan IA (donnees de sante,
allergenes) et la technique (modeles IA locaux) :

- CNIL (reglementaire, RGPD/IA)      - autorite administrative francaise
- EFSA (reglementaire, alimentaire)  - agence europeenne de securite des aliments
- Ollama releases sur GitHub (technique) - depot officiel du projet
- Hugging Face Blog (technique)      - reference des modeles IA open-source

Ce script outille la veille (etape de collecte), la synthese et les
recommandations qui en decoulent restent un travail d'analyse humaine,
redige dans docs/03-bloc2-ia/veille.md.

Dependances : feedparser (voir requirements.txt).

Usage :
    py -m veille.aggregate_veille

Resultat : ai-service/data/raw/veille/veille_<date>.json
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import feedparser

from common.io_utils import get_data_dir, setup_logger

logger = setup_logger("veille.aggregate_veille")

USER_AGENT = "NutriScanIA-Formation/0.1 (projet pedagogique Simplon DevIA; contact: nutriscan-ia@example.com)"
MAX_ENTRIES_PER_FEED = 8

FEEDS: list[dict[str, Any]] = [
    {
        "nom": "CNIL — Actualités",
        "url": "https://www.cnil.fr/fr/rss.xml",
        "theme": "reglementaire",
        "fiabilite": "Autorité administrative indépendante française (source institutionnelle de premier rang)",
        "mots_cles": ["intelligence artificielle", " ia ", "algorithm", "santé", "donnée de santé"],
    },
    {
        "nom": "EFSA — News",
        "url": "https://www.efsa.europa.eu/en/all/rss",
        "theme": "reglementaire",
        "fiabilite": "Agence européenne de sécurité des aliments (source institutionnelle de premier rang)",
        "mots_cles": ["allerg", "nutri", "label", "food information"],
    },
    {
        "nom": "Ollama — Releases GitHub",
        "url": "https://github.com/ollama/ollama/releases.atom",
        "theme": "technique",
        "fiabilite": "Dépôt officiel du projet open-source Ollama",
        "mots_cles": [],
    },
    {
        "nom": "Hugging Face — Blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "theme": "technique",
        "fiabilite": "Blog officiel de la plateforme de référence des modèles IA open-source",
        "mots_cles": [],
    },
]


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text or "").strip()


def _matches_keywords(entry_text: str, mots_cles: list[str]) -> bool:
    if not mots_cles:
        return True
    text_lower = entry_text.lower()
    return any(mot in text_lower for mot in mots_cles)


def fetch_feed(feed: dict[str, Any]) -> list[dict[str, str]]:
    parsed = feedparser.parse(feed["url"], agent=USER_AGENT)
    if parsed.bozo:
        logger.warning("Flux mal forme ou inaccessible : %s (%s)", feed["nom"], parsed.get("bozo_exception"))

    entries = []
    for raw_entry in parsed.entries:
        titre = raw_entry.get("title", "")
        resume = _strip_html(raw_entry.get("summary", ""))
        if not _matches_keywords(f"{titre} {resume}", feed["mots_cles"]):
            continue
        entries.append({
            "titre": titre,
            "lien": raw_entry.get("link", ""),
            "date": raw_entry.get("published", raw_entry.get("updated", "")),
            "resume": resume[:400],
        })
        if len(entries) >= MAX_ENTRIES_PER_FEED:
            break
    return entries


def run() -> Path:
    """Interroge les 4 flux de veille et sauvegarde les entrees pertinentes du jour."""
    output_dir = get_data_dir("raw", "veille")
    results: list[dict[str, Any]] = []

    for feed in FEEDS:
        try:
            entries = fetch_feed(feed)
        except Exception as exc:  # feedparser peut lever des erreurs reseau variees
            logger.warning("Echec de recuperation du flux %s : %s", feed["nom"], exc)
            entries = []
        logger.info("%s : %d entree(s) retenue(s)", feed["nom"], len(entries))
        results.append({
            "nom": feed["nom"],
            "url": feed["url"],
            "theme": feed["theme"],
            "fiabilite": feed["fiabilite"],
            "entrees": entries,
        })

    output_path = output_dir / f"veille_{date.today().isoformat()}.json"
    output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Veille sauvegardee dans %s", output_path)
    return output_path


if __name__ == "__main__":
    run()
