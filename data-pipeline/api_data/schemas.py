"""Modeles Pydantic de l'API Data (documentation OpenAPI generee automatiquement par FastAPI).

Note : ce projet cible Python 3.9 (contrainte de l'environnement de
developpement), qui ne supporte pas la syntaxe `X | None` dans les modeles
Pydantic (evaluee au runtime). On utilise donc `typing.Optional` plutot que
l'union par `|`.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class AllergeneOut(BaseModel):
    id_allergene: int
    libelle: str
    reference_reglementaire: str


class ProduitOut(BaseModel):
    code_barres: str
    nom: str
    marque: Optional[str] = None
    categorie: Optional[str] = None
    nutri_score: Optional[str] = None


class ProduitDetailOut(ProduitOut):
    ingredients_texte: str
    allergenes: list[str] = Field(default_factory=list)


class IngredientOut(BaseModel):
    libelle: str
    quantite: Optional[str] = None


class RecetteOut(BaseModel):
    id_recette: int
    titre: str
    source_url: str


class RecetteDetailOut(RecetteOut):
    instructions: Optional[str] = None
    ingredients: list[IngredientOut] = Field(default_factory=list)


class CompositionNutritionnelleOut(BaseModel):
    code_ciqual: str
    libelle_aliment: str
    energie_kcal: Optional[float] = None
    proteines_g: Optional[float] = None
    glucides_g: Optional[float] = None
    lipides_g: Optional[float] = None
