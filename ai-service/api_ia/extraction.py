"""Detection d'allergenes hybride (IA + mots-cles) et calcul du statut de compatibilite.

Approche retenue suite au POC (S5, voir docs/03-bloc2-ia/poc.md) : le
modele local (3B) rate certains allergenes pourtant nommes explicitement
dans le texte (ex. "sesame seed paste" non relie a "Graines de sesame").
Pour un cas d'usage ou un allergene manque a des consequences reelles pour
l'utilisateur, on ne se repose pas sur la seule IA : on ajoute une
recherche par mots-cles deterministe (le meme dictionnaire de synonymes que
celui donne en contexte au modele) et on retient l'**union** des deux
detections. Un faux positif occasionnel est prefere a un allergene non
signale.
"""
from __future__ import annotations

import json
import re
import unicodedata
from typing import Any

from openai import OpenAI, OpenAIError

from common.allergenes import ALLERGENES_REFERENTIEL, SYNONYMES_ALLERGENES

SYSTEM_PROMPT = f"""Tu es un assistant d'analyse d'etiquettes alimentaires.
On te fournit un texte (ingredients d'un produit ou d'une recette).
Identifie lesquels des allergenes suivants (referentiel officiel, reglement
UE 1169/2011) sont presents ou tres probablement presents dans le texte.
Pour chaque allergene, voici des synonymes/formes a reconnaitre meme s'ils
sont formules differemment dans le texte :
{chr(10).join(f"- {nom} : {', '.join(synonymes)}" for nom, synonymes in SYNONYMES_ALLERGENES.items())}

Reponds UNIQUEMENT avec un objet JSON de cette forme, sans aucun texte
autour :
{{"allergenes_detectes": ["Lait", "Gluten (cereales)"], "justification": "courte explication en une phrase"}}

N'invente jamais un allergene absent du texte. Utilise exactement les
libelles de la liste ci-dessus (aucune variante orthographique). Si aucun
allergene n'est detecte, renvoie une liste vide."""


def _normalize(text: str) -> str:
    """Minuscule, sans accents, et sans ligatures (oe/ae) pour une recherche de mots-cles fiable.

    NFKD decompose les caracteres accentues (e -> e + accent, filtre ensuite)
    mais NE decompose PAS les ligatures typographiques comme "oe" (U+0153) en
    "o"+"e" : sans ce remplacement explicite, "boeuf"/"oeuf" ecrits avec la
    ligature (tres frequent en francais correct) ne matchent jamais leur
    synonyme "oeuf" - bug reel trouve via le jeu de donnees de reference
    (golden_dataset), voir docs/03-bloc2-ia/tests-modele.md.
    """
    text = text.replace("œ", "oe").replace("Œ", "OE").replace("æ", "ae").replace("Æ", "AE")
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)).lower()


def _extract_json(raw_content: str) -> dict[str, Any]:
    try:
        return json.loads(raw_content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw_content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def detecter_par_mots_cles(texte: str) -> list[str]:
    """Recherche deterministe des allergenes via le dictionnaire de synonymes (filet de securite)."""
    texte_normalise = _normalize(texte)
    detectes = []
    for allergene, synonymes in SYNONYMES_ALLERGENES.items():
        if any(_normalize(synonyme) in texte_normalise for synonyme in synonymes):
            detectes.append(allergene)
    return detectes


def detecter_par_ia(client: OpenAI, model: str, texte: str) -> tuple[list[str], str]:
    """Interroge le modele local pour extraire les allergenes ; renvoie (allergenes, justification)."""
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": texte},
        ],
    )
    raw_content = response.choices[0].message.content
    try:
        parsed = _extract_json(raw_content)
    except (json.JSONDecodeError, AttributeError):
        return [], "reponse du modele non exploitable"

    detectes = [a for a in parsed.get("allergenes_detectes", []) if a in ALLERGENES_REFERENTIEL]
    return detectes, parsed.get("justification", "")


def analyser_texte(client: OpenAI, model: str, texte: str, allergies_utilisateur: list[dict[str, str]]) -> dict[str, Any]:
    """Analyse un texte et calcule le statut de compatibilite avec le profil fourni.

    `allergies_utilisateur` : liste de {"libelle": <allergene du referentiel>, "niveau": "allergie"|"intolerance"|"preference"}.
    Ce niveau (au sens Merise, voir docs/01-cadrage/merise.md) permet de distinguer une
    incompatibilite stricte (allergie) d'un simple risque (intolerance/preference).

    Le filet de securite par mots-cles est calcule en premier, independamment
    du modele : si l'appel au modele local echoue (Ollama indisponible), on
    degrade sur ce seul filet plutot que de faire echouer l'analyse entiere -
    bug reel trouve en simulant une panne d'Ollama (voir
    docs/04-bloc3-app/incident-resolution.md) : l'ancien code appelait le
    modele en premier et une erreur de connexion faisait echouer toute la
    fonction avant meme d'executer la recherche par mots-cles, qui ne
    necessite pourtant aucun reseau. Le champ `ia_disponible` du resultat
    signale explicitement ce mode degrade (jamais silencieux, voir US9).
    """
    detection_mots_cles = detecter_par_mots_cles(texte)
    try:
        detection_ia, justification = detecter_par_ia(client, model, texte)
        ia_disponible = True
    except OpenAIError:
        detection_ia, justification = [], (
            "Service IA temporairement indisponible : analyse basee uniquement sur la "
            "recherche de mots-cles, moins fiable (des allergenes formules de maniere "
            "inhabituelle peuvent ne pas etre detectes)."
        )
        ia_disponible = False
    allergenes_detectes = sorted(set(detection_ia) | set(detection_mots_cles))

    libelles_utilisateur = {a["libelle"]: a["niveau"] for a in allergies_utilisateur}
    problematiques = [a for a in allergenes_detectes if a in libelles_utilisateur]

    if any(libelles_utilisateur[a] == "allergie" for a in problematiques):
        statut = "incompatible"
    elif problematiques:
        statut = "a_risque"
    else:
        statut = "compatible"

    return {
        "statut_compatibilite": statut,
        "allergenes_detectes": allergenes_detectes,
        "allergenes_problematiques": sorted(problematiques),
        "detection_ia": sorted(detection_ia),
        "detection_mots_cles": sorted(detection_mots_cles),
        "justification_ia": justification,
        "ia_disponible": ia_disponible,
    }
