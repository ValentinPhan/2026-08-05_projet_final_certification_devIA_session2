"""Fixtures partagees des tests du backend applicatif."""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("APP_JWT_SECRET_KEY", "test-app-jwt-secret-au-moins-32-octets-de-long")
os.environ.setdefault("RGPD_ENCRYPTION_KEY", "test-rgpd-key")


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Vide le compteur d'echecs de connexion entre chaque test (etat en memoire, module-level)."""
    from backend.security import _tentatives_echouees
    _tentatives_echouees.clear()
    yield
    _tentatives_echouees.clear()
