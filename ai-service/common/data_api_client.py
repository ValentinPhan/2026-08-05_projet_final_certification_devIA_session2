"""Client minimal pour l'API Data (Bloc 1), reutilise par le POC (S5) puis l'API IA (S6).

Appelle l'API Data par HTTP comme le ferait n'importe quel autre consommateur
du systeme (voir docs/01-cadrage/architecture.md : les composants ne
communiquent qu'au travers de leurs API REST, jamais par import de code).
"""
from __future__ import annotations

import os
import time
from typing import Any

import requests
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

DATA_API_BASE_URL = os.environ.get("DATA_API_BASE_URL", "http://localhost:8010")

_cached_token: str | None = None
_cached_token_fetched_at: float = 0.0
_TOKEN_CACHE_TTL_SECONDS = 25 * 60  # jeton emis pour 30 min (voir api_data/auth.py) : marge de securite


def _client_credentials() -> tuple[str, str]:
    return (
        os.environ.get("API_CLIENT_ID", "nutriscan-app"),
        os.environ.get("API_CLIENT_SECRET", "change-moi-en-local"),
    )


def get_token() -> str:
    client_id, client_secret = _client_credentials()
    response = requests.post(
        f"{DATA_API_BASE_URL}/auth/token",
        params={"client_id": client_id, "client_secret": client_secret},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def get_cached_token() -> str:
    """Reutilise le jeton en cache tant qu'il n'approche pas son expiration, pour eviter
    de solliciter /auth/token a chaque requete entrante de l'API IA."""
    global _cached_token, _cached_token_fetched_at
    now = time.monotonic()
    if _cached_token is None or (now - _cached_token_fetched_at) > _TOKEN_CACHE_TTL_SECONDS:
        _cached_token = get_token()
        _cached_token_fetched_at = now
    return _cached_token


def _get(path: str, token: str, params: dict[str, Any] | None = None) -> Any:
    response = requests.get(
        f"{DATA_API_BASE_URL}{path}",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def list_produits(token: str, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
    return _get("/produits", token, {"limit": limit, "offset": offset})


def get_produit(token: str, code_barres: str) -> dict[str, Any]:
    return _get(f"/produits/{code_barres}", token)


def list_recettes(token: str, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
    return _get("/recettes", token, {"limit": limit, "offset": offset})


def get_recette(token: str, id_recette: int) -> dict[str, Any]:
    return _get(f"/recettes/{id_recette}", token)
