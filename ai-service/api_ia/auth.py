"""Authentification et limitation de debit de l'API IA (C9, securite OWASP API).

Meme schema "client credentials" que l'API Data (voir
data-pipeline/api_data/auth.py) : l'API IA est consommee par d'autres
composants du systeme, pas directement par un utilisateur final.

Limitation de debit ajoutee ici specifiquement (absente de l'API Data) car
cette API declenche une inference sur un modele local a chaque appel — une
ressource couteuse en temps de calcul. Cible explicitement OWASP API4:2023
"Unrestricted Resource Consumption". Implementation en memoire (fenetre
fixe par client), suffisante pour une instance unique de developpement ;
une mise a l'echelle multi-instance necessiterait un compteur partage
(ex. Redis), note comme limite connue.
"""
from __future__ import annotations

import os
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
RATE_LIMIT_MAX_APPELS = 20
RATE_LIMIT_FENETRE_SECONDES = 60

_bearer_scheme = HTTPBearer(auto_error=True)
_appels_par_client: dict[str, list[float]] = defaultdict(list)


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


def enforce_rate_limit(client_id: str = Depends(require_valid_token)) -> str:
    """Dependance FastAPI : limite le nombre d'appels par client sur une fenetre glissante."""
    now = time.monotonic()
    horodatages = _appels_par_client[client_id]
    horodatages[:] = [t for t in horodatages if now - t < RATE_LIMIT_FENETRE_SECONDES]

    if len(horodatages) >= RATE_LIMIT_MAX_APPELS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Limite de {RATE_LIMIT_MAX_APPELS} appels par {RATE_LIMIT_FENETRE_SECONDES}s depassee",
        )
    horodatages.append(now)
    return client_id
