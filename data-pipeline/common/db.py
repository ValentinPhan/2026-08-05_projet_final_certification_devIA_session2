"""Connexion PostgreSQL partagee par le script d'import et l'API Data."""
from __future__ import annotations

import os

import psycopg2
from dotenv import find_dotenv, load_dotenv
from psycopg2.extensions import connection as PgConnection

# find_dotenv() remonte les dossiers parents pour trouver le .env a la racine
# du depot, meme lorsque le script est lance depuis data-pipeline/.
load_dotenv(find_dotenv())


def get_connection() -> PgConnection:
    """Ouvre une connexion PostgreSQL a partir de la variable d'environnement DATABASE_URL."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL manquante : copier .env.example vers .env a la racine du depot et l'adapter."
        )
    return psycopg2.connect(database_url)
