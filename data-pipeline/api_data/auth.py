"""Authentification de l'API Data par jeton JWT (competence C5, securite OWASP API).

L'API Data est consommee par d'autres composants du systeme (l'application du
Bloc 3, l'API IA du Bloc 2), pas directement par un utilisateur final : il ne
s'agit donc pas d'une authentification par identifiant/mot de passe
utilisateur (celle-ci vit dans l'application, Bloc 3), mais d'un schema
« client credentials » simple entre services de confiance du systeme.

Securite (OWASP API Top 10) :
- Le secret client et la cle de signature JWT sont lus depuis l'environnement
  (jamais codes en dur), voir .env.example.
- Les jetons expirent (30 minutes) pour limiter la fenetre d'exploitation
  d'un jeton compromis.
- Un jeton invalide ou expire renvoie 401 sans detail sur la cause exacte
  (pas d'information exploitable pour un attaquant).
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

_bearer_scheme = HTTPBearer(auto_error=True)


def _secret_key() -> str:
    key = os.environ.get("JWT_SECRET_KEY")
    if not key:
        raise RuntimeError("JWT_SECRET_KEY manquante : copier .env.example vers .env et l'adapter.")
    return key


def _expected_client_credentials() -> tuple[str, str]:
    client_id = os.environ.get("API_CLIENT_ID", "nutriscan-app")
    client_secret = os.environ.get("API_CLIENT_SECRET", "change-moi-en-local")
    return client_id, client_secret


def authenticate_client(client_id: str, client_secret: str) -> bool:
    expected_id, expected_secret = _expected_client_credentials()
    return client_id == expected_id and client_secret == expected_secret


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, _secret_key(), algorithm=ALGORITHM)


def require_valid_token(credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme)) -> str:
    """Dependance FastAPI : verifie le jeton Bearer, leve 401 s'il est absent/invalide/expire."""
    try:
        payload = jwt.decode(credentials.credentials, _secret_key(), algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Jeton invalide ou expire")
    return payload["sub"]
