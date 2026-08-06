"""Modeles Pydantic de l'API IA (documentation OpenAPI generee automatiquement par FastAPI).

Note : comme pour l'API Data, `typing.Optional`/`Literal` sont utilises a la
place de la syntaxe `X | None` (PEP 604), non supportee au runtime par
Pydantic v2 sur l'environnement Python 3.9 cible.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

NiveauAllergie = Literal["allergie", "intolerance", "preference"]


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class AllergieUtilisateurIn(BaseModel):
    libelle: str = Field(..., description="Libelle exact du referentiel des 14 allergenes (voir GET /allergenes de l'API Data)")
    niveau: NiveauAllergie = Field(..., description="allergie = incompatible, intolerance/preference = a_risque")


class AnalyseTexteIn(BaseModel):
    texte: str = Field(..., min_length=1, max_length=5000, description="Texte d'ingredients a analyser")
    allergies_utilisateur: list[AllergieUtilisateurIn] = Field(default_factory=list)


class AnalyseProduitIn(BaseModel):
    allergies_utilisateur: list[AllergieUtilisateurIn] = Field(default_factory=list)


class AnalyseRecetteIn(BaseModel):
    allergies_utilisateur: list[AllergieUtilisateurIn] = Field(default_factory=list)


class AnalyseOut(BaseModel):
    statut_compatibilite: Literal["compatible", "a_risque", "incompatible"]
    allergenes_detectes: list[str]
    allergenes_problematiques: list[str]
    detection_ia: list[str]
    detection_mots_cles: list[str]
    justification_ia: str
    # False si le modele local (Ollama) etait indisponible au moment de
    # l'analyse : le resultat ne repose alors que sur le filet de securite
    # par mots-cles (voir extraction.py::analyser_texte, incident S11).
    ia_disponible: bool = True


class AnalyseProduitOut(AnalyseOut):
    code_barres: str
    nom: str


class AnalyseRecetteOut(AnalyseOut):
    id_recette: int
    titre: str
