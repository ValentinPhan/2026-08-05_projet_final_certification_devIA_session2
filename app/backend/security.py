"""Securite du backend applicatif (C17 ; OWASP Top 10 Web / API Top 10).

Schema d'authentification distinct de celui utilise entre services
(data-pipeline/api_data/auth.py, ai-service/api_ia/auth.py) : la-bas, un
schema "client credentials" simple suffit car les appelants sont d'autres
composants de confiance du systeme. Ici, l'appelant est un utilisateur final
qui s'authentifie avec un email et un mot de passe - d'ou un secret de
signature JWT dedie (APP_JWT_SECRET_KEY, distinct de JWT_SECRET_KEY) : un
jeton de session utilisateur compromis ne doit jamais pouvoir etre rejoue
comme jeton de service, et inversement.
"""
from __future__ import annotations

import os
import re
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# OWASP API4:2023 "Unrestricted Resource Consumption" applique ici a
# /auth/connexion (bruteforce de mot de passe) plutot qu'a une ressource de
# calcul couteuse (cf. limitation de debit de l'API IA, motif different mais
# meme principe d'implementation - fenetre glissante en memoire).
RATE_LIMIT_MAX_TENTATIVES = 5
RATE_LIMIT_FENETRE_SECONDES = 15 * 60

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MOT_DE_PASSE_LONGUEUR_MIN = 10
# bcrypt tronque/rejette au-dela de 72 octets (limite native de l'algorithme) :
# borne haute imposee ici plutot que laissee provoquer une ValueError au hachage.
MOT_DE_PASSE_LONGUEUR_MAX = 72

_bearer_scheme = HTTPBearer(auto_error=True)
_tentatives_echouees: dict[str, list[float]] = defaultdict(list)

# Hash de reference utilise pour normaliser le temps de reponse de /auth/connexion
# quand l'email n'existe pas (evite qu'un attaquant deduise l'existence d'un
# compte a partir du temps de calcul bcrypt reellement effectue ou non).
_HASH_FACTICE = bcrypt.hashpw(b"mot-de-passe-de-reference-jamais-utilise-01", bcrypt.gensalt()).decode("ascii")


def _secret_key() -> str:
    key = os.environ.get("APP_JWT_SECRET_KEY")
    if not key:
        raise RuntimeError("APP_JWT_SECRET_KEY manquante : copier .env.example vers .env et l'adapter.")
    return key


def email_valide(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email))


def mot_de_passe_robuste(mot_de_passe: str) -> bool:
    """Regle de robustesse minimale (OWASP ASVS 2.1) : longueur + melange lettres/chiffres."""
    if not (MOT_DE_PASSE_LONGUEUR_MIN <= len(mot_de_passe) <= MOT_DE_PASSE_LONGUEUR_MAX):
        return False
    return any(c.isalpha() for c in mot_de_passe) and any(c.isdigit() for c in mot_de_passe)


def hacher_mot_de_passe(mot_de_passe: str) -> str:
    return bcrypt.hashpw(mot_de_passe.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verifier_mot_de_passe(mot_de_passe: str, hash_stocke: str | None) -> bool:
    """Verifie un mot de passe ; verifie contre un hash factice si `hash_stocke` est None
    (email inconnu) pour que le temps de reponse ne revele pas l'existence du compte."""
    resultat = bcrypt.checkpw(mot_de_passe.encode("utf-8"), (hash_stocke or _HASH_FACTICE).encode("ascii"))
    return resultat and hash_stocke is not None


def creer_jeton_session(id_utilisateur: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(id_utilisateur), "exp": expire}
    return jwt.encode(payload, _secret_key(), algorithm=ALGORITHM)


def utilisateur_courant(credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme)) -> int:
    """Dependance FastAPI : verifie le jeton de session, renvoie l'id_utilisateur porteur."""
    try:
        payload = jwt.decode(credentials.credentials, _secret_key(), algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session invalide ou expiree")
    return int(payload["sub"])


def verrouille_pour_bruteforce(email: str) -> bool:
    """Verifie la fenetre glissante d'echecs de connexion pour cet email.

    Implementation en memoire (mono-instance) : limite connue et deja
    documentee pour un cas similaire (voir ai-service/api_ia/auth.py) - une
    mise a l'echelle multi-instance necessiterait un compteur partage
    (ex. Redis).
    """
    now = time.monotonic()
    echecs = _tentatives_echouees[email]
    echecs[:] = [t for t in echecs if now - t < RATE_LIMIT_FENETRE_SECONDES]
    return len(echecs) >= RATE_LIMIT_MAX_TENTATIVES


def enregistrer_echec_connexion(email: str) -> None:
    _tentatives_echouees[email].append(time.monotonic())


def reinitialiser_echecs_connexion(email: str) -> None:
    _tentatives_echouees.pop(email, None)
