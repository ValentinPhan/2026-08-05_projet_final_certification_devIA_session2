"""Tests unitaires de la logique hybride IA + mots-cles (api_ia/extraction.py).

Seul l'appel au modele (`detecter_par_ia`) est simule : la logique de
detection par mots-cles, l'union des deux sources et le calcul du statut de
compatibilite sont, eux, reellement executes — ce sont les tests qui
comptent le plus ici, la fiabilite du modele ayant deja ete mesuree
empiriquement lors du POC (voir docs/03-bloc2-ia/poc.md).
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest
from openai import APIConnectionError

from api_ia.extraction import analyser_texte, detecter_par_ia, detecter_par_mots_cles


def test_detecter_par_mots_cles_trouve_synonyme():
    texte = "Cooked Chickpeas, Water, Tahini Sesame Seed Paste, Garlic, Salt."
    assert "Graines de sesame" in detecter_par_mots_cles(texte)


def test_detecter_par_mots_cles_insensible_aux_accents_et_a_la_casse():
    texte = "PURÉE DE SÉSAME, sel"
    assert "Graines de sesame" in detecter_par_mots_cles(texte)


def test_detecter_par_mots_cles_aucun_allergene():
    texte = "Eau, sucre, sel, aromes naturels."
    assert detecter_par_mots_cles(texte) == []


def test_analyser_texte_union_ia_et_mots_cles():
    """Meme quand l'IA ne retourne rien, les mots-cles rattrapent les allergenes explicites (cas reel du POC)."""
    client = MagicMock()
    with patch("api_ia.extraction.detecter_par_ia", return_value=([], "aucun allergene detecte")):
        resultat = analyser_texte(
            client, "modele-factice",
            "Tahini (sesame), eau, sel.",
            allergies_utilisateur=[],
        )
    assert resultat["allergenes_detectes"] == ["Graines de sesame"]
    assert resultat["detection_ia"] == []
    assert resultat["detection_mots_cles"] == ["Graines de sesame"]


def test_statut_incompatible_si_allergie_stricte():
    client = MagicMock()
    with patch("api_ia.extraction.detecter_par_ia", return_value=([], "")):
        resultat = analyser_texte(
            client, "modele-factice", "Lait entier, sucre.",
            allergies_utilisateur=[{"libelle": "Lait", "niveau": "allergie"}],
        )
    assert resultat["statut_compatibilite"] == "incompatible"
    assert resultat["allergenes_problematiques"] == ["Lait"]


def test_statut_a_risque_si_intolerance_ou_preference():
    client = MagicMock()
    with patch("api_ia.extraction.detecter_par_ia", return_value=([], "")):
        resultat = analyser_texte(
            client, "modele-factice", "Lait entier, sucre.",
            allergies_utilisateur=[{"libelle": "Lait", "niveau": "intolerance"}],
        )
    assert resultat["statut_compatibilite"] == "a_risque"


def test_statut_compatible_si_aucun_allergene_declare_detecte():
    client = MagicMock()
    with patch("api_ia.extraction.detecter_par_ia", return_value=([], "")):
        resultat = analyser_texte(
            client, "modele-factice", "Eau, sucre, sel.",
            allergies_utilisateur=[{"libelle": "Lait", "niveau": "allergie"}],
        )
    assert resultat["statut_compatibilite"] == "compatible"
    assert resultat["allergenes_problematiques"] == []


def test_analyser_texte_degrade_sur_mots_cles_si_ia_indisponible():
    """Incident reel simule (S11, panne d'Ollama) : l'ancienne version faisait
    echouer toute l'analyse (500) des que l'appel au modele levait une
    exception, y compris pour la recherche par mots-cles qui ne necessite
    pourtant aucun reseau. Voir docs/04-bloc3-app/incident-resolution.md."""
    client = MagicMock()
    erreur = APIConnectionError(request=httpx.Request("POST", "http://ollama-indisponible/v1/chat/completions"))
    with patch("api_ia.extraction.detecter_par_ia", side_effect=erreur):
        resultat = analyser_texte(
            client, "modele-factice",
            "Tahini (sesame), eau, sel.",
            allergies_utilisateur=[{"libelle": "Graines de sesame", "niveau": "allergie"}],
        )
    assert resultat["ia_disponible"] is False
    assert resultat["detection_ia"] == []
    assert resultat["detection_mots_cles"] == ["Graines de sesame"]
    assert resultat["allergenes_detectes"] == ["Graines de sesame"]
    assert resultat["statut_compatibilite"] == "incompatible"
    assert "indisponible" in resultat["justification_ia"].lower()


def test_analyser_texte_ia_disponible_a_true_en_fonctionnement_normal():
    client = MagicMock()
    with patch("api_ia.extraction.detecter_par_ia", return_value=(["Lait"], "detecte")):
        resultat = analyser_texte(client, "modele-factice", "lait", allergies_utilisateur=[])
    assert resultat["ia_disponible"] is True


def test_detecter_par_ia_filtre_les_allergenes_hors_referentiel():
    """Un allergene hallucine par le modele hors du referentiel officiel est filtre."""
    faux_client = MagicMock()
    faux_message = MagicMock()
    faux_message.content = '{"allergenes_detectes": ["Ananas", "Lait"], "justification": "test"}'
    faux_client.chat.completions.create.return_value.choices = [MagicMock(message=faux_message)]

    detectes, _ = detecter_par_ia(faux_client, "modele-factice", "peu importe")

    assert detectes == ["Lait"]
