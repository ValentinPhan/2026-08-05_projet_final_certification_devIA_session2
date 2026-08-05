"""API REST IA de NutriScan IA (Bloc 2, competences C9/C10).

Expose l'analyse de compatibilite allergene (extraction hybride IA + mots-cles,
voir `extraction.py`) aux autres composants du systeme (prototype Streamlit
S6, puis application Bloc 3).

Documentation interactive generee automatiquement par FastAPI (norme
OpenAPI) : http://localhost:8011/docs une fois le serveur lance.

Perimetre de securite : comme l'API Data, cette API n'expose et ne modifie
aucune donnee personnelle. Le profil allergene transmis dans le corps des
requetes n'est utilise que dans le code de comparaison ci-dessous (jamais
inclus dans le prompt envoye au modele) — seul le texte d'ingredients/de
recette (donnee publique) est transmis a l'IA.

Usage (developpement) :
    cd ai-service
    py -m uvicorn api_ia.main:app --reload --port 8011
"""
from __future__ import annotations

import os

import requests
from openai import OpenAI

from fastapi import Depends, FastAPI, HTTPException

from common.data_api_client import get_cached_token, get_produit, get_recette
from .auth import authenticate_client, create_access_token, enforce_rate_limit, ACCESS_TOKEN_EXPIRE_MINUTES
from .extraction import analyser_texte
from .schemas import (
    AnalyseOut,
    AnalyseProduitIn,
    AnalyseProduitOut,
    AnalyseRecetteIn,
    AnalyseRecetteOut,
    AnalyseTexteIn,
    TokenOut,
)

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
MODEL_NAME = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")

app = FastAPI(
    title="NutriScan IA — API IA",
    description="Analyse la compatibilite allergene d'un produit/d'une recette avec un profil alimentaire.",
    version="0.1.0",
)

_ollama_client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")


@app.get("/health", tags=["monitoring"], summary="Verifie que l'API est en ligne")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/token", response_model=TokenOut, tags=["auth"], summary="Obtenir un jeton d'acces")
def issue_token(client_id: str, client_secret: str) -> TokenOut:
    if not authenticate_client(client_id, client_secret):
        raise HTTPException(status_code=401, detail="Identifiants client invalides")
    token = create_access_token(subject=client_id)
    return TokenOut(access_token=token, expires_in_minutes=ACCESS_TOKEN_EXPIRE_MINUTES)


@app.post(
    "/analyser/texte",
    response_model=AnalyseOut,
    tags=["analyse"],
    dependencies=[Depends(enforce_rate_limit)],
    summary="Analyse un texte libre (ingredients) par rapport a un profil allergene",
)
def analyser_texte_endpoint(payload: AnalyseTexteIn) -> AnalyseOut:
    resultat = analyser_texte(
        _ollama_client, MODEL_NAME, payload.texte,
        [a.model_dump() for a in payload.allergies_utilisateur],
    )
    return AnalyseOut(**resultat)


@app.post(
    "/analyser/produit/{code_barres}",
    response_model=AnalyseProduitOut,
    tags=["analyse"],
    dependencies=[Depends(enforce_rate_limit)],
    summary="Analyse un produit (recupere via l'API Data) par rapport a un profil allergene",
)
def analyser_produit_endpoint(code_barres: str, payload: AnalyseProduitIn) -> AnalyseProduitOut:
    try:
        produit = get_produit(get_cached_token(), code_barres)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Produit introuvable") from None
        raise HTTPException(status_code=502, detail=f"API Data indisponible : {exc}") from None
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"API Data indisponible : {exc}") from None

    resultat = analyser_texte(
        _ollama_client, MODEL_NAME, produit["ingredients_texte"],
        [a.model_dump() for a in payload.allergies_utilisateur],
    )
    return AnalyseProduitOut(code_barres=produit["code_barres"], nom=produit["nom"], **resultat)


@app.post(
    "/analyser/recette/{id_recette}",
    response_model=AnalyseRecetteOut,
    tags=["analyse"],
    dependencies=[Depends(enforce_rate_limit)],
    summary="Analyse une recette (recuperee via l'API Data) par rapport a un profil allergene",
)
def analyser_recette_endpoint(id_recette: int, payload: AnalyseRecetteIn) -> AnalyseRecetteOut:
    try:
        recette = get_recette(get_cached_token(), id_recette)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Recette introuvable") from None
        raise HTTPException(status_code=502, detail=f"API Data indisponible : {exc}") from None
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"API Data indisponible : {exc}") from None

    texte = "\n".join(f"{i['libelle']} {i.get('quantite') or ''}" for i in recette["ingredients"])
    resultat = analyser_texte(
        _ollama_client, MODEL_NAME, texte,
        [a.model_dump() for a in payload.allergies_utilisateur],
    )
    return AnalyseRecetteOut(id_recette=recette["id_recette"], titre=recette["titre"], **resultat)
