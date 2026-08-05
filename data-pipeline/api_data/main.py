"""API REST Data de NutriScan IA (Bloc 1, competence C5).

Expose en lecture les donnees collectees et nettoyees au Bloc 1 (produits,
recettes, table de composition nutritionnelle, referentiel des allergenes)
aux autres composants du systeme (application Bloc 3, service IA Bloc 2).

Documentation interactive generee automatiquement par FastAPI (norme
OpenAPI) : http://localhost:8010/docs une fois le serveur lance.

Perimetre de securite volontaire : cette API n'expose et ne modifie AUCUNE
donnee personnelle (pas de comptes, pas de profils allergenes utilisateur,
pas d'historique) - ces donnees relevent exclusivement de l'application
(Bloc 3) et de sa propre base. Toutes les routes de donnees exigent malgre
tout un jeton Bearer valide (voir `auth.py`), par defense en profondeur.

Usage (developpement) :
    cd data-pipeline
    py -m uvicorn api_data.main:app --reload --port 8010
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import connection as PgConnection

from common.db import get_connection
from .auth import authenticate_client, create_access_token, require_valid_token, ACCESS_TOKEN_EXPIRE_MINUTES
from .schemas import (
    AllergeneOut,
    CompositionNutritionnelleOut,
    IngredientOut,
    ProduitDetailOut,
    ProduitOut,
    RecetteDetailOut,
    RecetteOut,
    TokenOut,
)

app = FastAPI(
    title="NutriScan IA — API Data",
    description="Expose les donnees produits, recettes, nutrition et allergenes collectees au Bloc 1.",
    version="0.1.0",
)


@contextmanager
def _db_cursor() -> Iterator[RealDictCursor]:
    conn: PgConnection = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
    finally:
        conn.close()


def get_cursor() -> Iterator[RealDictCursor]:
    with _db_cursor() as cur:
        yield cur


@app.get("/health", tags=["monitoring"], summary="Verifie que l'API est en ligne")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/token", response_model=TokenOut, tags=["auth"], summary="Obtenir un jeton d'acces")
def issue_token(client_id: str, client_secret: str) -> TokenOut:
    if not authenticate_client(client_id, client_secret):
        raise HTTPException(status_code=401, detail="Identifiants client invalides")
    token = create_access_token(subject=client_id)
    return TokenOut(access_token=token, expires_in_minutes=ACCESS_TOKEN_EXPIRE_MINUTES)


@app.get(
    "/allergenes",
    response_model=list[AllergeneOut],
    tags=["allergenes"],
    dependencies=[Depends(require_valid_token)],
    summary="Referentiel officiel des 14 allergenes a declaration obligatoire",
)
def list_allergenes(cur: RealDictCursor = Depends(get_cursor)) -> list[AllergeneOut]:
    cur.execute("SELECT id_allergene, libelle, reference_reglementaire FROM allergene ORDER BY libelle")
    return [AllergeneOut(**row) for row in cur.fetchall()]


@app.get(
    "/produits",
    response_model=list[ProduitOut],
    tags=["produits"],
    dependencies=[Depends(require_valid_token)],
    summary="Liste les produits, avec filtres optionnels",
)
def list_produits(
    categorie: Optional[str] = Query(None, description="Filtre par categorie (correspondance partielle)"),
    nutri_score: Optional[str] = Query(None, min_length=1, max_length=1, description="Filtre par Nutri-Score (a-e)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    cur: RealDictCursor = Depends(get_cursor),
) -> list[ProduitOut]:
    query = "SELECT code_barres, nom, marque, categorie, nutri_score FROM produit WHERE true"
    params: list[object] = []
    if categorie:
        query += " AND categorie ILIKE %s"
        params.append(f"%{categorie}%")
    if nutri_score:
        query += " AND nutri_score = %s"
        params.append(nutri_score.lower())
    query += " ORDER BY nom LIMIT %s OFFSET %s"
    params += [limit, offset]
    cur.execute(query, params)
    return [ProduitOut(**row) for row in cur.fetchall()]


@app.get(
    "/produits/{code_barres}",
    response_model=ProduitDetailOut,
    tags=["produits"],
    dependencies=[Depends(require_valid_token)],
    summary="Detail d'un produit, avec ses allergenes",
)
def get_produit(code_barres: str, cur: RealDictCursor = Depends(get_cursor)) -> ProduitDetailOut:
    cur.execute(
        "SELECT code_barres, nom, marque, categorie, nutri_score, ingredients_texte "
        "FROM produit WHERE code_barres = %s",
        (code_barres,),
    )
    produit = cur.fetchone()
    if produit is None:
        raise HTTPException(status_code=404, detail="Produit introuvable")

    cur.execute(
        "SELECT a.libelle FROM produit_allergene pa "
        "JOIN allergene a ON a.id_allergene = pa.id_allergene "
        "WHERE pa.code_barres = %s ORDER BY a.libelle",
        (code_barres,),
    )
    allergenes = [row["libelle"] for row in cur.fetchall()]
    return ProduitDetailOut(**produit, allergenes=allergenes)


@app.get(
    "/recettes",
    response_model=list[RecetteOut],
    tags=["recettes"],
    dependencies=[Depends(require_valid_token)],
    summary="Liste les recettes collectees",
)
def list_recettes(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    cur: RealDictCursor = Depends(get_cursor),
) -> list[RecetteOut]:
    cur.execute(
        "SELECT id_recette, titre, source_url FROM recette ORDER BY titre LIMIT %s OFFSET %s",
        (limit, offset),
    )
    return [RecetteOut(**row) for row in cur.fetchall()]


@app.get(
    "/recettes/{id_recette}",
    response_model=RecetteDetailOut,
    tags=["recettes"],
    dependencies=[Depends(require_valid_token)],
    summary="Detail d'une recette, avec ses ingredients",
)
def get_recette(id_recette: int, cur: RealDictCursor = Depends(get_cursor)) -> RecetteDetailOut:
    cur.execute(
        "SELECT id_recette, titre, source_url, instructions FROM recette WHERE id_recette = %s",
        (id_recette,),
    )
    recette = cur.fetchone()
    if recette is None:
        raise HTTPException(status_code=404, detail="Recette introuvable")

    cur.execute(
        "SELECT i.libelle, ri.quantite FROM recette_ingredient ri "
        "JOIN ingredient i ON i.id_ingredient = ri.id_ingredient "
        "WHERE ri.id_recette = %s",
        (id_recette,),
    )
    ingredients = [IngredientOut(**row) for row in cur.fetchall()]
    return RecetteDetailOut(**recette, ingredients=ingredients)


@app.get(
    "/nutrition/{code_ciqual}",
    response_model=CompositionNutritionnelleOut,
    tags=["nutrition"],
    dependencies=[Depends(require_valid_token)],
    summary="Composition nutritionnelle officielle (Ciqual) d'un aliment",
)
def get_nutrition(code_ciqual: str, cur: RealDictCursor = Depends(get_cursor)) -> CompositionNutritionnelleOut:
    cur.execute(
        "SELECT code_ciqual, libelle_aliment, energie_kcal, proteines_g, glucides_g, lipides_g "
        "FROM composition_nutritionnelle WHERE code_ciqual = %s",
        (code_ciqual,),
    )
    row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Aliment Ciqual introuvable")
    return CompositionNutritionnelleOut(**row)
