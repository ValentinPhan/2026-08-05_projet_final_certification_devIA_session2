"""Tests de l'API IA (contrat des endpoints, authentification, gestion d'erreurs).

L'appel au modele local et l'appel a l'API Data sont simules ici : ce fichier
teste le cablage de l'API (routes, auth, codes de statut), pas la qualite de
l'extraction (voir test_extraction.py) ni la disponibilite reelle d'Ollama/de
l'API Data (verifiees manuellement en conditions reelles, voir
docs/03-bloc2-ia/api-ia.md).
"""
from __future__ import annotations

from unittest.mock import patch

import requests
from fastapi.testclient import TestClient

from api_ia.main import app

client = TestClient(app)

RESULTAT_FACTICE = {
    "statut_compatibilite": "compatible",
    "allergenes_detectes": [],
    "allergenes_problematiques": [],
    "detection_ia": [],
    "detection_mots_cles": [],
    "justification_ia": "",
}


def _jeton_valide() -> str:
    response = client.post(
        "/auth/token",
        params={"client_id": "nutriscan-app", "client_secret": "test-secret"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_health_sans_authentification():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_token_avec_identifiants_invalides():
    response = client.post("/auth/token", params={"client_id": "x", "client_secret": "y"})
    assert response.status_code == 401


def test_token_avec_identifiants_valides():
    token = _jeton_valide()
    assert token


def test_analyser_texte_sans_jeton_refuse():
    response = client.post("/analyser/texte", json={"texte": "lait, sucre"})
    assert response.status_code in (401, 403)  # selon la version de Starlette/HTTPBearer


def test_analyser_texte_avec_jeton_invalide_refuse():
    response = client.post(
        "/analyser/texte", json={"texte": "lait, sucre"},
        headers={"Authorization": "Bearer jeton-invalide"},
    )
    assert response.status_code == 401


def test_analyser_texte_ok():
    token = _jeton_valide()
    with patch("api_ia.main.analyser_texte", return_value=RESULTAT_FACTICE):
        response = client.post(
            "/analyser/texte",
            json={"texte": "eau, sucre", "allergies_utilisateur": []},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    assert response.json()["statut_compatibilite"] == "compatible"


def test_analyser_produit_introuvable_renvoie_404():
    token = _jeton_valide()
    erreur_404 = requests.HTTPError(response=requests.Response())
    erreur_404.response.status_code = 404
    with patch("api_ia.main.get_cached_token", return_value="jeton-data-api"), \
         patch("api_ia.main.get_produit", side_effect=erreur_404):
        response = client.post(
            "/analyser/produit/0000000000000",
            json={"allergies_utilisateur": []},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 404


def test_analyser_produit_trouve_ok():
    token = _jeton_valide()
    produit_factice = {
        "code_barres": "123",
        "nom": "Produit test",
        "ingredients_texte": "eau, sucre",
    }
    with patch("api_ia.main.get_cached_token", return_value="jeton-data-api"), \
         patch("api_ia.main.get_produit", return_value=produit_factice), \
         patch("api_ia.main.analyser_texte", return_value=RESULTAT_FACTICE):
        response = client.post(
            "/analyser/produit/123",
            json={"allergies_utilisateur": [{"libelle": "Lait", "niveau": "allergie"}]},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["code_barres"] == "123"
    assert body["nom"] == "Produit test"


def test_analyser_recette_introuvable_renvoie_404():
    token = _jeton_valide()
    erreur_404 = requests.HTTPError(response=requests.Response())
    erreur_404.response.status_code = 404
    with patch("api_ia.main.get_cached_token", return_value="jeton-data-api"), \
         patch("api_ia.main.get_recette", side_effect=erreur_404):
        response = client.post(
            "/analyser/recette/9999",
            json={"allergies_utilisateur": []},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 404


def test_api_data_indisponible_renvoie_502():
    token = _jeton_valide()
    with patch("api_ia.main.get_cached_token", return_value="jeton-data-api"), \
         patch("api_ia.main.get_produit", side_effect=requests.ConnectionError("API Data injoignable")):
        response = client.post(
            "/analyser/produit/123",
            json={"allergies_utilisateur": []},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 502


def test_limite_de_debit_declenchee():
    """Au-dela de RATE_LIMIT_MAX_APPELS appels sur la fenetre, l'API renvoie 429."""
    from api_ia.auth import RATE_LIMIT_MAX_APPELS

    token = _jeton_valide()
    with patch("api_ia.main.analyser_texte", return_value=RESULTAT_FACTICE):
        for _ in range(RATE_LIMIT_MAX_APPELS):
            response = client.post(
                "/analyser/texte", json={"texte": "eau"},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200
        derniere_reponse = client.post(
            "/analyser/texte", json={"texte": "eau"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert derniere_reponse.status_code == 429
