"""Tests d'integration du prototype (C10) : couvrent tous les points de
terminaison des API Data et IA effectivement exploites par
`frontend/prototype.py`.

Contrairement aux tests unitaires de l'API IA (mockes, voir
ai-service/api_ia/tests/), ces tests appellent la **vraie** stack en cours
d'execution (`docker compose up -d`, Ollama demarre) : ils verifient
l'integration reelle, pas seulement le contrat de chaque API isolement.
Plus lents (l'analyse IA prend 15-30s), a executer manuellement plutot que
dans un pipeline CI rapide.

Prerequis :
    docker compose up -d
    ollama serve  (+ modele tire)

Usage :
    cd app
    py -m pytest tests/test_integration.py -v
"""
from __future__ import annotations

import os

import pytest
import requests
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

DATA_API_URL = os.environ.get("DATA_API_BASE_URL", "http://localhost:8010")
IA_API_URL = os.environ.get("IA_API_BASE_URL", "http://localhost:8011")
CLIENT_ID = os.environ.get("API_CLIENT_ID", "nutriscan-app")
CLIENT_SECRET = os.environ.get("API_CLIENT_SECRET", "change-moi-en-local")


def _stack_disponible() -> bool:
    try:
        return (
            requests.get(f"{DATA_API_URL}/health", timeout=3).status_code == 200
            and requests.get(f"{IA_API_URL}/health", timeout=3).status_code == 200
        )
    except requests.RequestException:
        return False


pytestmark = pytest.mark.skipif(
    not _stack_disponible(),
    reason="Stack Docker (API Data + API IA) non demarree : `docker compose up -d`",
)


def _jeton(base_url: str) -> str:
    response = requests.post(
        f"{base_url}/auth/token",
        params={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def test_auth_data_api():
    assert _jeton(DATA_API_URL)


def test_auth_api_ia():
    assert _jeton(IA_API_URL)


def test_lister_allergenes():
    token = _jeton(DATA_API_URL)
    response = requests.get(f"{DATA_API_URL}/allergenes", headers={"Authorization": f"Bearer {token}"}, timeout=10)
    assert response.status_code == 200
    allergenes = response.json()
    assert len(allergenes) == 14
    assert "Lait" in [a["libelle"] for a in allergenes]


def test_lister_produits():
    token = _jeton(DATA_API_URL)
    response = requests.get(
        f"{DATA_API_URL}/produits", headers={"Authorization": f"Bearer {token}"},
        params={"limit": 5}, timeout=10,
    )
    assert response.status_code == 200
    produits = response.json()
    assert len(produits) > 0
    assert "code_barres" in produits[0]


def test_lister_recettes():
    token = _jeton(DATA_API_URL)
    response = requests.get(
        f"{DATA_API_URL}/recettes", headers={"Authorization": f"Bearer {token}"},
        params={"limit": 5}, timeout=10,
    )
    assert response.status_code == 200
    recettes = response.json()
    assert len(recettes) > 0
    assert "id_recette" in recettes[0]


def test_analyser_texte_bout_en_bout():
    """Cas reel qui a revele un bug d'origine multilingue (produit allemand,
    voir docs/03-bloc2-ia/prototype.md) : verifie que le lait est desormais
    detecte dans un texte d'ingredients en allemand."""
    token = _jeton(IA_API_URL)
    response = requests.post(
        f"{IA_API_URL}/analyser/texte",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "texte": "Weizenmehl, Wasser, Edamer (Milch, Speisesalz)",
            "allergies_utilisateur": [{"libelle": "Lait", "niveau": "allergie"}],
        },
        timeout=60,
    )
    assert response.status_code == 200
    resultat = response.json()
    assert resultat["statut_compatibilite"] == "incompatible"
    assert "Lait" in resultat["allergenes_problematiques"]


def test_analyser_produit_reel():
    token_data = _jeton(DATA_API_URL)
    produits = requests.get(
        f"{DATA_API_URL}/produits", headers={"Authorization": f"Bearer {token_data}"},
        params={"limit": 1}, timeout=10,
    ).json()
    code_barres = produits[0]["code_barres"]

    token_ia = _jeton(IA_API_URL)
    response = requests.post(
        f"{IA_API_URL}/analyser/produit/{code_barres}",
        headers={"Authorization": f"Bearer {token_ia}"},
        json={"allergies_utilisateur": []},
        timeout=60,
    )
    assert response.status_code == 200
    assert response.json()["code_barres"] == code_barres


def test_analyser_recette_reelle():
    token_data = _jeton(DATA_API_URL)
    recettes = requests.get(
        f"{DATA_API_URL}/recettes", headers={"Authorization": f"Bearer {token_data}"},
        params={"limit": 1}, timeout=10,
    ).json()
    id_recette = recettes[0]["id_recette"]

    token_ia = _jeton(IA_API_URL)
    response = requests.post(
        f"{IA_API_URL}/analyser/recette/{id_recette}",
        headers={"Authorization": f"Bearer {token_ia}"},
        json={"allergies_utilisateur": []},
        timeout=60,
    )
    assert response.status_code == 200
    assert response.json()["id_recette"] == id_recette


def test_analyser_produit_introuvable():
    token_ia = _jeton(IA_API_URL)
    response = requests.post(
        f"{IA_API_URL}/analyser/produit/0000000000000",
        headers={"Authorization": f"Bearer {token_ia}"},
        json={"allergies_utilisateur": []},
        timeout=15,
    )
    assert response.status_code == 404
