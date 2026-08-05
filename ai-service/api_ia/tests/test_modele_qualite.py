"""Tests automatises du modele IA (competence C12).

Perimetre et strategie de test (voir docs/03-bloc2-ia/tests-modele.md pour
le detail) :

1. **Validation du jeu de donnees de reference** (rapide) : le golden
   dataset lui-meme doit etre coherent (allergenes attendus tous dans le
   referentiel officiel, textes non vides, identifiants uniques) avant de
   servir de base a toute evaluation.
2. **Non-regression de la detection par mots-cles** (rapide, sans appel
   reseau) : chaque cas du golden dataset doit etre correctement traite par
   le filet de securite deterministe. C'est ce test qui aurait immediatement
   detecte les bugs trouves manuellement en S6-S7 (terme allemand trop
   court, mots anglais manquants, synonymes trop generiques) sans attendre
   un test manuel.
3. **Evaluation globale du pipeline hybride** (lent, necessite Ollama) :
   mesure precision/rappel reels sur le golden dataset et verifie qu'ils
   restent au-dessus d'un seuil plancher, informe par la mesure empirique du
   POC (S5) plutot qu'arbitraire. Ce test est celui qui detecterait une
   regression si un changement de modele/prompt degradait la qualite.
"""
from __future__ import annotations

import time

import pytest
from openai import OpenAI

from common.allergenes import ALLERGENES_REFERENTIEL
from common.golden_dataset import CAS_EVALUATION
from api_ia.extraction import analyser_texte, detecter_par_mots_cles

OLLAMA_BASE_URL = "http://localhost:11434/v1"
MODEL_NAME = "llama3.2:3b"

# Seuils plancher informes par la mesure empirique sur ce golden dataset
# (voir docs/03-bloc2-ia/monitoring-modele.md pour le detail). Le filet de
# mots-cles a lui seul atteint 100% precision/rappel sur ce jeu ; l'IA y
# ajoute un biais systematique de sur-detection du gluten (y compris sur un
# jus de fruits sans aucun rapport), ce qui degrade la precision globale
# sans jamais ameliorer le rappel ici. Les seuils reproduisent ce constat
# reel (~67% precision, 100% rappel) plutot qu'un objectif aspirationnel :
# le test doit detecter une **regression** (un modele qui deviendrait pire),
# pas imposer une qualite non encore atteinte.
SEUIL_PRECISION_MINIMUM = 0.60
SEUIL_RAPPEL_MINIMUM = 0.95


def _ollama_disponible() -> bool:
    try:
        import requests
        return requests.get("http://localhost:11434/", timeout=2).status_code == 200
    except Exception:
        return False


def test_golden_dataset_structure_valide():
    """Le jeu de donnees de reference est lui-meme coherent avant de servir de base d'evaluation."""
    identifiants = [cas["id"] for cas in CAS_EVALUATION]
    assert len(identifiants) == len(set(identifiants)), "identifiants de cas dupliques"
    assert len(CAS_EVALUATION) >= 10, "jeu de reference trop petit pour etre representatif"

    for cas in CAS_EVALUATION:
        assert cas["texte"].strip(), f"{cas['id']} : texte vide"
        for allergene in cas["allergenes_attendus"]:
            assert allergene in ALLERGENES_REFERENTIEL, f"{cas['id']} : '{allergene}' hors referentiel officiel"


@pytest.mark.parametrize("cas", CAS_EVALUATION, ids=[c["id"] for c in CAS_EVALUATION])
def test_detection_mots_cles_sur_jeu_de_reference(cas):
    """Non-regression du filet de securite deterministe : rapide, aucun appel reseau."""
    detectes = set(detecter_par_mots_cles(cas["texte"]))
    attendus = set(cas["allergenes_attendus"])
    assert detectes == attendus, (
        f"{cas['id']} ({cas['description']}) : detectes={sorted(detectes)} attendus={sorted(attendus)}"
    )


@pytest.mark.skipif(not _ollama_disponible(), reason="Ollama non demarre (ollama serve)")
def test_evaluation_hybride_seuils_minimums():
    """Evaluation du pipeline complet (IA + mots-cles) sur le golden dataset, avec le vrai modele.

    Lent (une inference par cas, ~10-25s chacune) : c'est le meme calcul que
    celui journalise dans MLflow par ai-service/monitoring/evaluer_modele.py
    (C11), rejoue ici comme porte de qualite automatisee (C12).
    """
    client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
    vrais_positifs = faux_positifs = faux_negatifs = 0

    for cas in CAS_EVALUATION:
        resultat = analyser_texte(client, MODEL_NAME, cas["texte"], allergies_utilisateur=[])
        detectes = set(resultat["allergenes_detectes"])
        attendus = set(cas["allergenes_attendus"])
        vrais_positifs += len(detectes & attendus)
        faux_positifs += len(detectes - attendus)
        faux_negatifs += len(attendus - detectes)

    precision = vrais_positifs / (vrais_positifs + faux_positifs) if (vrais_positifs + faux_positifs) else 1.0
    rappel = vrais_positifs / (vrais_positifs + faux_negatifs) if (vrais_positifs + faux_negatifs) else 1.0

    assert precision >= SEUIL_PRECISION_MINIMUM, f"precision {precision:.0%} sous le seuil {SEUIL_PRECISION_MINIMUM:.0%}"
    assert rappel >= SEUIL_RAPPEL_MINIMUM, f"rappel {rappel:.0%} sous le seuil {SEUIL_RAPPEL_MINIMUM:.0%}"
