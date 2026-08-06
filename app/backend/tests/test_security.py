"""Tests unitaires de la securite du backend (hachage, JWT, robustesse, anti-bruteforce).

Aucun de ces tests ne touche la base de donnees : ce sont des fonctions pures
ou en memoire (voir backend/security.py).
"""
from __future__ import annotations

import time

import jwt
import pytest

from backend.security import (
    creer_jeton_session,
    email_valide,
    enregistrer_echec_connexion,
    hacher_mot_de_passe,
    mot_de_passe_robuste,
    utilisateur_courant,
    verifier_mot_de_passe,
    verrouille_pour_bruteforce,
    RATE_LIMIT_MAX_TENTATIVES,
)


def test_email_valide_accepte_un_email_correct():
    assert email_valide("utilisateur@example.com")


@pytest.mark.parametrize("email", ["sans-arobase.com", "sans-domaine@", "@sans-local.com", "avec espace@example.com"])
def test_email_valide_rejette_un_email_incorrect(email):
    assert not email_valide(email)


@pytest.mark.parametrize("mot_de_passe", ["Court1", "aaaaaaaaaa", "1234567890", "MotDePasse123"])
def test_mot_de_passe_robuste(mot_de_passe):
    attendu = mot_de_passe == "MotDePasse123"
    assert mot_de_passe_robuste(mot_de_passe) is attendu


def test_hachage_puis_verification_reussit():
    hash_ = hacher_mot_de_passe("MotDePasse123")
    assert hash_ != "MotDePasse123"
    assert verifier_mot_de_passe("MotDePasse123", hash_)


def test_verification_echoue_avec_mauvais_mot_de_passe():
    hash_ = hacher_mot_de_passe("MotDePasse123")
    assert not verifier_mot_de_passe("AutreMotDePasse456", hash_)


def test_verification_email_inconnu_renvoie_faux_sans_lever():
    """hash_stocke=None (email inexistant) : ne doit jamais lever, toujours renvoyer False."""
    assert not verifier_mot_de_passe("MotDePasse123", None)


def test_jeton_session_contient_le_bon_sujet():
    jeton = creer_jeton_session(id_utilisateur=42)
    payload = jwt.decode(jeton, options={"verify_signature": False})
    assert payload["sub"] == "42"


def test_utilisateur_courant_accepte_un_jeton_valide():
    from fastapi.security import HTTPAuthorizationCredentials
    jeton = creer_jeton_session(id_utilisateur=7)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=jeton)
    assert utilisateur_courant(credentials) == 7


def test_utilisateur_courant_rejette_un_jeton_invalide():
    from fastapi import HTTPException
    from fastapi.security import HTTPAuthorizationCredentials
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="jeton-invalide")
    with pytest.raises(HTTPException) as exc_info:
        utilisateur_courant(credentials)
    assert exc_info.value.status_code == 401


def test_verrouillage_apres_trop_de_tentatives():
    email = "bruteforce-unitaire@example.com"
    assert not verrouille_pour_bruteforce(email)
    for _ in range(RATE_LIMIT_MAX_TENTATIVES):
        enregistrer_echec_connexion(email)
    assert verrouille_pour_bruteforce(email)
