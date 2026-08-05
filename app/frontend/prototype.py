"""Prototype Streamlit — NutriScan IA (Bloc 2, competence C10).

Demontre l'integration de l'API IA (S6) et de l'API Data (Bloc 1) dans une
interface utilisateur : recherche d'un produit ou d'une recette (ou saisie
d'un texte libre), declaration d'un profil allergene, et affichage du
resultat d'analyse de compatibilite.

Ce prototype n'est pas l'application finale (Bloc 3, S9) : pas de compte
utilisateur ni de persistance du profil - le profil allergene est saisi a
chaque session, exactement comme les API elles-memes ne connaissent aucune
notion de compte (voir docs/03-bloc2-ia/api-ia.md, perimetre de securite).

Dependances : streamlit, requests, python-dotenv (voir requirements.txt).

Usage :
    cd app
    py -m streamlit run frontend/prototype.py
"""
from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

DATA_API_URL = os.environ.get("DATA_API_BASE_URL", "http://localhost:8010")
IA_API_URL = os.environ.get("IA_API_BASE_URL", "http://localhost:8011")
CLIENT_ID = os.environ.get("API_CLIENT_ID", "nutriscan-app")
CLIENT_SECRET = os.environ.get("API_CLIENT_SECRET", "change-moi-en-local")

STATUT_AFFICHAGE = {
    "compatible": ("✅", "Compatible", "success"),
    "a_risque": ("⚠️", "À risque", "warning"),
    "incompatible": ("⛔", "Incompatible", "error"),
}


def _token(base_url: str) -> str | None:
    """Recupere (et met en cache dans la session) un jeton pour l'API donnee."""
    cle_cache = f"token::{base_url}"
    if cle_cache in st.session_state:
        return st.session_state[cle_cache]
    try:
        response = requests.post(
            f"{base_url}/auth/token",
            params={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET},
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        st.session_state[f"erreur::{base_url}"] = str(exc)
        return None
    token = response.json()["access_token"]
    st.session_state[cle_cache] = token
    return token


def _appel_api(base_url: str, methode: str, chemin: str, timeout: int = 15, **kwargs: Any) -> Any:
    """Appelle l'API donnee avec le jeton courant ; renvoie None et affiche une alerte en cas d'echec.

    `timeout` par defaut court (15s, appels API Data) ; les appels a l'API IA
    (voir `analyser`) passent un timeout plus genereux : une inference locale
    peut prendre 15-25s en regime normal, davantage apres un rechargement a
    froid du modele (Ollama le decharge de la memoire au bout de quelques
    minutes d'inactivite, voir docs/03-bloc2-ia/poc.md) — constate lors des
    tests manuels de ce prototype, corrige ici plutot que suppose.
    """
    token = _token(base_url)
    if token is None:
        st.error(f"Service indisponible ({base_url}) : {st.session_state.get(f'erreur::{base_url}', '')}")
        return None
    try:
        response = requests.request(
            methode, f"{base_url}{chemin}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout, **kwargs,
        )
        if response.status_code == 401:
            # Jeton expire ou invalide : on force son renouvellement et on retente une fois.
            del st.session_state[f"token::{base_url}"]
            token = _token(base_url)
            response = requests.request(
                methode, f"{base_url}{chemin}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=timeout, **kwargs,
            )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        st.error(f"Le service n'a pas pu repondre : {exc}")
        return None


def analyser(chemin: str, **kwargs: Any) -> Any:
    """Appelle l'API IA avec un timeout genereux (inference locale, potentiellement lente a froid)."""
    with st.spinner("Analyse en cours (peut prendre jusqu'à une minute la première fois)…"):
        return _appel_api(IA_API_URL, "POST", chemin, timeout=90, **kwargs)


@st.cache_data(ttl=300)
def charger_allergenes_referentiel() -> list[dict[str, Any]]:
    resultat = _appel_api(DATA_API_URL, "GET", "/allergenes")
    return resultat or []


def afficher_resultat(resultat: dict[str, Any]) -> None:
    icone, libelle, niveau = STATUT_AFFICHAGE[resultat["statut_compatibilite"]]
    getattr(st, niveau)(f"{icone} **{libelle}**")

    if resultat["allergenes_problematiques"]:
        st.markdown("**Allergènes posant problème avec votre profil :** " + ", ".join(resultat["allergenes_problematiques"]))
    if resultat["allergenes_detectes"]:
        st.markdown("**Tous les allergènes détectés :** " + ", ".join(resultat["allergenes_detectes"]))
    else:
        st.markdown("Aucun allergène détecté dans ce texte.")

    with st.expander("Détail de la détection (transparence de l'analyse)"):
        st.markdown(f"- Détectés par l'IA : {', '.join(resultat['detection_ia']) or 'aucun'}")
        st.markdown(f"- Détectés par recherche de mots-clés (filet de sécurité) : {', '.join(resultat['detection_mots_cles']) or 'aucun'}")
        if resultat["justification_ia"]:
            st.markdown(f"- Justification du modèle : _{resultat['justification_ia']}_")


def saisir_profil_allergene() -> list[dict[str, str]]:
    referentiel = charger_allergenes_referentiel()
    libelles = [a["libelle"] for a in referentiel]

    st.subheader("Mon profil alimentaire")
    allergies = st.multiselect("Allergies (incompatibilité stricte)", libelles, key="allergies")
    intolerances = st.multiselect("Intolérances / préférences (à risque)", libelles, key="intolerances")

    profil = [{"libelle": a, "niveau": "allergie"} for a in allergies]
    profil += [{"libelle": a, "niveau": "intolerance"} for a in intolerances if a not in allergies]
    return profil


def main() -> None:
    st.set_page_config(page_title="NutriScan IA — Prototype", page_icon="🥗")
    st.title("NutriScan IA — prototype")
    st.warning(
        "⚠️ Cet outil est une aide à la lecture d'étiquettes et de recettes. "
        "Il ne constitue en aucun cas un avis médical."
    )

    profil = saisir_profil_allergene()

    st.divider()
    onglet_produit, onglet_recette, onglet_texte = st.tabs(["Produit", "Recette", "Texte libre"])

    with onglet_produit:
        recherche = st.text_input("Filtrer par catégorie (ex. « biscuit »)", key="recherche_produit")
        produits = _appel_api(DATA_API_URL, "GET", "/produits", params={"categorie": recherche, "limit": 20}) or []
        if produits:
            options = {f"{p['nom']} ({p['code_barres']})": p["code_barres"] for p in produits}
            choix = st.selectbox("Produit", list(options.keys()))
            if st.button("Analyser ce produit"):
                resultat = analyser(
                    f"/analyser/produit/{options[choix]}",
                    json={"allergies_utilisateur": profil},
                )
                if resultat is None:
                    st.error("Produit introuvable ou service indisponible.")
                else:
                    afficher_resultat(resultat)
        else:
            st.info("Aucun produit trouvé pour ce filtre.")

    with onglet_recette:
        recettes = _appel_api(DATA_API_URL, "GET", "/recettes", params={"limit": 20}) or []
        if recettes:
            options = {r["titre"]: r["id_recette"] for r in recettes}
            choix = st.selectbox("Recette", list(options.keys()))
            if st.button("Analyser cette recette"):
                resultat = analyser(
                    f"/analyser/recette/{options[choix]}",
                    json={"allergies_utilisateur": profil},
                )
                if resultat is None:
                    st.error("Recette introuvable ou service indisponible.")
                else:
                    afficher_resultat(resultat)
        else:
            st.info("Aucune recette disponible.")

    with onglet_texte:
        texte = st.text_area("Coller une liste d'ingrédients", height=120)
        if st.button("Analyser ce texte") and texte.strip():
            resultat = analyser(
                "/analyser/texte",
                json={"texte": texte, "allergies_utilisateur": profil},
            )
            if resultat is not None:
                afficher_resultat(resultat)


if __name__ == "__main__":
    main()
