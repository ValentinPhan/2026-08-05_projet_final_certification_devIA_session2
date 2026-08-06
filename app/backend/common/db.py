"""Connexion PostgreSQL du backend applicatif (Bloc 3, competence C17).

Ce backend est le seul composant autorise a lire/ecrire les tables de
donnees personnelles (utilisateur, utilisateur_allergene,
analyse_compatibilite, traitement_rgpd). Il partage la meme instance
PostgreSQL que data-pipeline (voir docker-compose.yml, un seul conteneur
`postgres` pour tout le systeme) mais ne touche jamais aux tables du
catalogue (produit, recette, ingredient, composition_nutritionnelle),
exclusivement gerees par l'API Data - voir docs/04-bloc3-app/dev-application.md
(section architecture) pour la justification de ce partage d'instance avec
separation stricte par table plutot que deux bases physiques distinctes.
"""
from __future__ import annotations

import os

import psycopg2
from dotenv import find_dotenv, load_dotenv
from psycopg2.extensions import connection as PgConnection

load_dotenv(find_dotenv())


def get_connection() -> PgConnection:
    """Ouvre une connexion PostgreSQL a partir de la variable d'environnement DATABASE_URL."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL manquante : copier .env.example vers .env a la racine du depot et l'adapter."
        )
    return psycopg2.connect(database_url)
