"""POC — extraction d'allergenes par IA locale (Ollama), competence C8.

Teste la faisabilite du service retenu au benchmark (voir
docs/03-bloc2-ia/benchmark-services-ia.md) sur un vrai jeu de donnees :
recupere des produits reels via l'API Data (Bloc 1, deja en service),
demande au modele local d'identifier lesquels des 14 allergenes officiels
sont presents dans le texte d'ingredients, et compare le resultat aux
allergenes deja references par Open Food Facts (verite terrain approximative
- Open Food Facts n'est pas non plus exhaustif ni infaillible).

Prerequis :
- Ollama installe et demarre (`ollama serve`), modele tire (`ollama pull llama3.2:3b`)
- Stack Docker du Bloc 1 demarree (`docker compose up -d`) et alimentee
  (`py -m load.import_data` depuis data-pipeline/)

Dependances : openai (client pointe sur l'API compatible OpenAI d'Ollama),
requests, python-dotenv (voir requirements.txt).

Usage :
    py -m poc.extraction_poc

Resultat : ai-service/data/raw/poc/extraction_poc_results.json
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from openai import OpenAI

from common.allergenes import ALLERGENES_REFERENTIEL, SYNONYMES_ALLERGENES
from common.data_api_client import get_produit, get_token, list_produits
from common.io_utils import get_data_dir, setup_logger

logger = setup_logger("poc.extraction_poc")

OLLAMA_BASE_URL = "http://localhost:11434/v1"
MODEL_NAME = "llama3.2:3b"
NB_PRODUITS_TESTES = 10

SYSTEM_PROMPT = f"""Tu es un assistant d'analyse d'etiquettes alimentaires.
On te fournit la liste d'ingredients d'un produit. Identifie lesquels des
allergenes suivants (referentiel officiel, reglement UE 1169/2011) sont
presents ou tres probablement presents dans le texte. Pour chaque
allergene, voici des synonymes/formes a reconnaitre meme s'ils sont
formules differemment dans le texte :
{chr(10).join(f"- {nom} : {', '.join(synonymes)}" for nom, synonymes in SYNONYMES_ALLERGENES.items())}

Reponds UNIQUEMENT avec un objet JSON de cette forme, sans aucun texte
autour :
{{"allergenes_detectes": ["Lait", "Gluten (cereales)"], "justification": "courte explication en une phrase"}}

N'invente jamais un allergene absent du texte. Utilise exactement les
libelles de la liste ci-dessus (aucune variante orthographique). Si aucun
allergene n'est detecte, renvoie une liste vide."""


def _extract_json(raw_content: str) -> dict[str, Any]:
    """Extrait l'objet JSON de la reponse du modele, avec un repli si du texte l'entoure."""
    try:
        return json.loads(raw_content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw_content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def analyser_ingredients(client: OpenAI, ingredients_texte: str) -> dict[str, Any]:
    """Appelle le modele local pour extraire les allergenes d'un texte d'ingredients."""
    response = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": ingredients_texte},
        ],
    )
    raw_content = response.choices[0].message.content
    try:
        parsed = _extract_json(raw_content)
    except (json.JSONDecodeError, AttributeError) as exc:
        logger.warning("Reponse non JSON du modele, ignoree : %s (%s)", raw_content, exc)
        return {"allergenes_detectes": [], "justification": "reponse du modele non exploitable"}

    detectes = [a for a in parsed.get("allergenes_detectes", []) if a in ALLERGENES_REFERENTIEL]
    ignores = set(parsed.get("allergenes_detectes", [])) - set(detectes)
    if ignores:
        logger.warning("Allergene(s) hors referentiel ignore(s) : %s", ignores)
    return {"allergenes_detectes": detectes, "justification": parsed.get("justification", "")}


def run() -> Path:
    """Teste l'extraction d'allergenes sur un echantillon de produits reels du Bloc 1."""
    client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
    token = get_token()

    produits = list_produits(token, limit=NB_PRODUITS_TESTES)
    resultats = []
    vrais_positifs = faux_positifs = faux_negatifs = 0

    for resume in produits:
        detail = get_produit(token, resume["code_barres"])
        verite_terrain = set(detail["allergenes"])

        analyse = analyser_ingredients(client, detail["ingredients_texte"])
        detectes = set(analyse["allergenes_detectes"])

        vp = detectes & verite_terrain
        fp = detectes - verite_terrain
        fn = verite_terrain - detectes
        vrais_positifs += len(vp)
        faux_positifs += len(fp)
        faux_negatifs += len(fn)

        logger.info(
            "%s : detectes=%s | attendus (OFF)=%s | VP=%d FP=%d FN=%d",
            detail["nom"][:40], sorted(detectes), sorted(verite_terrain), len(vp), len(fp), len(fn),
        )
        resultats.append({
            "code_barres": detail["code_barres"],
            "nom": detail["nom"],
            "ingredients_texte": detail["ingredients_texte"],
            "allergenes_attendus_open_food_facts": sorted(verite_terrain),
            "allergenes_detectes_ia": sorted(detectes),
            "justification_ia": analyse["justification"],
        })

    precision = vrais_positifs / (vrais_positifs + faux_positifs) if (vrais_positifs + faux_positifs) else None
    rappel = vrais_positifs / (vrais_positifs + faux_negatifs) if (vrais_positifs + faux_negatifs) else None
    logger.info(
        "Bilan sur %d produits : VP=%d FP=%d FN=%d | precision=%s rappel=%s",
        len(produits), vrais_positifs, faux_positifs, faux_negatifs,
        f"{precision:.0%}" if precision is not None else "n/a",
        f"{rappel:.0%}" if rappel is not None else "n/a",
    )

    output_path = get_data_dir("raw", "poc") / "extraction_poc_results.json"
    output_path.write_text(json.dumps({
        "modele": MODEL_NAME,
        "nb_produits_testes": len(produits),
        "vrais_positifs": vrais_positifs,
        "faux_positifs": faux_positifs,
        "faux_negatifs": faux_negatifs,
        "precision": precision,
        "rappel": rappel,
        "details": resultats,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Resultats sauvegardes dans %s", output_path)
    return output_path


if __name__ == "__main__":
    run()
