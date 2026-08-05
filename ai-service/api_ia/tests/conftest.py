"""Fixtures partagees des tests de l'API IA."""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("API_CLIENT_ID", "nutriscan-app")
os.environ.setdefault("API_CLIENT_SECRET", "test-secret")


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Vide le compteur de limitation de debit entre chaque test (etat en memoire, module-level)."""
    from api_ia.auth import _appels_par_client
    _appels_par_client.clear()
    yield
    _appels_par_client.clear()
