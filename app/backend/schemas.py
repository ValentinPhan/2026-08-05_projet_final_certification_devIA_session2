"""Modeles Pydantic du backend applicatif (C17).

Note : ce projet cible aussi Python 3.9 en developpement local (voir
data-pipeline/api_data/schemas.py) - on utilise donc `typing.Optional`
plutot que la syntaxe `X | None`, non supportee a l'execution par Pydantic
v2 sous 3.9.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

NiveauAllergene = Literal["allergie", "intolerance", "preference"]
StatutCompatibilite = Literal["compatible", "a_risque", "incompatible"]


class InscriptionIn(BaseModel):
    email: str
    mot_de_passe: str
    consentement_rgpd: bool
    consentement_donnee_sante: bool


class InscriptionOut(BaseModel):
    id_utilisateur: int
    email: str


class ConnexionIn(BaseModel):
    email: str
    mot_de_passe: str


class SessionOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class ProfilAllergeneIn(BaseModel):
    libelle: str
    niveau: NiveauAllergene


class ProfilAllergeneOut(BaseModel):
    libelle: str
    niveau: NiveauAllergene
    date_maj: datetime


class HistoriqueIn(BaseModel):
    code_barres: Optional[str] = None
    id_recette: Optional[int] = None
    statut_compatibilite: StatutCompatibilite
    allergenes_detectes: list[str] = Field(default_factory=list)
    substitutions_proposees: Optional[str] = None


class HistoriqueOut(BaseModel):
    id_analyse: int
    code_barres: Optional[str] = None
    id_recette: Optional[int] = None
    statut_compatibilite: StatutCompatibilite
    allergenes_detectes: list[str] = Field(default_factory=list)
    date_analyse: datetime


class UtilisateurOut(BaseModel):
    id_utilisateur: int
    email: str
    date_inscription: datetime
    consentement_rgpd: bool
    consentement_donnee_sante: bool


class ExportRgpdOut(BaseModel):
    utilisateur: UtilisateurOut
    profil_allergene: list[ProfilAllergeneOut]
    historique: list[HistoriqueOut]
