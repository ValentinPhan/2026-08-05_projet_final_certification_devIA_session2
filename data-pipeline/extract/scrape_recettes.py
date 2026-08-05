"""Collecte de recettes par scraping sur le Wikibooks francophone "Livre de cuisine".

Source choisie deliberement : le contenu de Wikibooks est publie sous licence
libre (CC BY-SA), ce qui leve toute ambiguite sur le droit de reutiliser le
texte collecte dans un projet pedagogique, contrairement a la plupart des
sites de recettes commerciaux dont les conditions d'utilisation interdisent
le scraping. Le fichier robots.txt du site est verifie programmatiquement
avant toute requete (voir `_check_robots_txt`).

Dependances : requests, beautifulsoup4, lxml (voir requirements.txt).

Usage :
    py extract/scrape_recettes.py

Resultat :
    data-pipeline/data/raw/recettes/<slug>.html   (page brute, pour tracabilite)
    data-pipeline/data/raw/recettes/recettes.json (donnees structurees)
"""
from __future__ import annotations

import json
import time
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from common.io_utils import get_data_dir, setup_logger

logger = setup_logger("extract.scrape_recettes")

USER_AGENT = "NutriScanIA-Formation/0.1 (projet pedagogique Simplon DevIA; contact: nutriscan-ia@example.com)"
HEADERS = {"User-Agent": USER_AGENT}

WIKI_HOST = "https://fr.wikibooks.org"
ROBOTS_URL = f"{WIKI_HOST}/robots.txt"
BASE_PATH = "/wiki/Livre_de_cuisine/"

REQUEST_DELAY_SECONDS = 1.0
REQUEST_TIMEOUT_SECONDS = 15

# Recettes verifiees manuellement (page existante) lors du cadrage de la
# collecte : constituent un corpus varie (entrees, plats, desserts).
RECIPE_TITLES = [
    "Ratatouille",
    "Quiche lorraine",
    "Tarte aux pommes",
    "Soupe à l'oignon",
    "Blanquette de veau",
    "Couscous",
    "Tarte Tatin",
    "Croque-monsieur",
    "Salade niçoise",
    "Cassoulet",
]


def _check_robots_txt() -> RobotFileParser:
    """Verifie les regles de robots.txt avant tout scraping (contrainte technique/legale, C1).

    On recupere le fichier via `requests` (avec notre en-tete `User-Agent`)
    plutot que `RobotFileParser.read()` : ce dernier utilise l'agent
    generique d'urllib, que certains sites (dont Wikimedia) bloquent avec un
    403 — ce qui ferait passer `disallow_all` a True et bloquerait a tort
    toute la collecte.
    """
    parser = RobotFileParser()
    parser.set_url(ROBOTS_URL)
    response = requests.get(ROBOTS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    parser.parse(response.text.splitlines())
    return parser


def _build_url(title: str) -> str:
    slug = title.replace(" ", "_")
    return WIKI_HOST + BASE_PATH + quote(slug, safe="_-")


def _normalize(text: str) -> str:
    """Supprime les accents et met en minuscule pour comparer les titres de section sans erreur."""
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)).lower()


def _fetch(url: str) -> str | None:
    for attempt in range(1, 4):
        try:
            response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        except requests.RequestException as exc:
            logger.warning("Erreur reseau (tentative %d/3) sur %s : %s", attempt, url, exc)
            time.sleep(attempt * REQUEST_DELAY_SECONDS)
            continue
        if response.status_code == 404:
            logger.warning("Page introuvable (404) : %s", url)
            return None
        if not response.ok:
            logger.warning("Reponse %d (tentative %d/3) sur %s", response.status_code, attempt, url)
            time.sleep(attempt * REQUEST_DELAY_SECONDS)
            continue
        return response.text
    logger.warning("Abandon apres 3 tentatives sur %s", url)
    return None


def _parse_recipe(html: str, source_url: str) -> dict[str, Any] | None:
    """Extrait titre, ingredients et instructions d'une page de recette Wikibooks."""
    soup = BeautifulSoup(html, "lxml")
    heading_el = soup.select_one("#firstHeading")
    content = soup.select_one("#mw-content-text .mw-parser-output")
    if heading_el is None or content is None:
        return None

    title = heading_el.get_text(strip=True)
    ingredients: list[str] = []
    steps: list[str] = []
    section = ""

    for element in content.find_all(["h2", "h3", "ul", "ol"]):
        if element.name in ("h2", "h3"):
            section = _normalize(element.get_text(strip=True))
            continue
        items = [li.get_text(" ", strip=True) for li in element.find_all("li", recursive=False)]
        if not items:
            continue
        if not ingredients and "ingredient" in section:
            ingredients = items
        elif not steps and ("preparation" in section or "etape" in section):
            steps = items

    if not ingredients:
        logger.warning("Aucun ingredient trouve pour %s (structure de page inattendue)", source_url)
        return None

    return {
        "titre": title,
        "source_url": source_url,
        "ingredients_bruts": ingredients,
        "instructions": steps,
    }


def run() -> Path:
    """Scrape le corpus de recettes cible et sauvegarde les pages brutes + les donnees structurees."""
    robots = _check_robots_txt()
    raw_dir = get_data_dir("raw", "recettes")
    recipes: list[dict[str, Any]] = []

    for title in RECIPE_TITLES:
        url = _build_url(title)
        if not robots.can_fetch(USER_AGENT, url):
            logger.warning("robots.txt interdit l'acces a %s : page ignoree", url)
            continue

        html = _fetch(url)
        time.sleep(REQUEST_DELAY_SECONDS)
        if html is None:
            continue

        slug = title.replace(" ", "_").replace("'", "")
        (raw_dir / f"{slug}.html").write_text(html, encoding="utf-8")

        recipe = _parse_recipe(html, url)
        if recipe is not None:
            recipes.append(recipe)
            logger.info(
                "Recette '%s' : %d ingredient(s), %d etape(s)",
                recipe["titre"], len(recipe["ingredients_bruts"]), len(recipe["instructions"]),
            )

    output_path = raw_dir / "recettes.json"
    output_path.write_text(json.dumps(recipes, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("%d recette(s) sauvegardee(s) dans %s", len(recipes), output_path)
    return output_path


if __name__ == "__main__":
    run()
