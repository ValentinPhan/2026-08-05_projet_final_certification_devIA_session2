"""Backend applicatif de NutriScan IA (Bloc 3, competence C17).

Possede et est seul a ecrire les donnees personnelles du systeme : compte
utilisateur, profil allergene (donnee de sante, RGPD art. 9), historique
d'analyses, journal de tracabilite RGPD (voir docs/rgpd/registre-traitements.md).
Le frontend Streamlit (`app/frontend/main.py`) ne se connecte jamais
directement a PostgreSQL : il appelle ce backend en HTTP exactement comme il
appelle l'API Data et l'API IA (voir docs/01-cadrage/architecture.md), ce qui
garde le principe "aucun composant n'accede directement a la base d'un
autre" - ici applique par composant/table plutot que par instance physique,
les trois API partageant le meme serveur PostgreSQL (docker-compose.yml).

Documentation interactive : http://localhost:8012/docs une fois lance.

Usage (developpement) :
    cd app
    py -m uvicorn backend.main:app --reload --port 8012
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from fastapi import Depends, FastAPI, HTTPException, Query, status
from psycopg2.extensions import connection as PgConnection
from psycopg2.extras import RealDictCursor

from .common.db import get_connection
from .schemas import (
    ConnexionIn,
    ExportRgpdOut,
    HistoriqueIn,
    HistoriqueOut,
    InscriptionIn,
    InscriptionOut,
    ProfilAllergeneIn,
    ProfilAllergeneOut,
    SessionOut,
    UtilisateurOut,
)
from .security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    creer_jeton_session,
    email_valide,
    enregistrer_echec_connexion,
    hacher_mot_de_passe,
    mot_de_passe_robuste,
    reinitialiser_echecs_connexion,
    utilisateur_courant,
    verifier_mot_de_passe,
    verrouille_pour_bruteforce,
)

app = FastAPI(
    title="NutriScan IA — Backend applicatif",
    description="Compte utilisateur, profil allergene, historique et droits RGPD (Bloc 3).",
    version="0.1.0",
)


def _cle_chiffrement() -> str:
    key = os.environ.get("RGPD_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("RGPD_ENCRYPTION_KEY manquante : copier .env.example vers .env et l'adapter.")
    return key


@contextmanager
def _db_cursor() -> Iterator[RealDictCursor]:
    conn: PgConnection = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_cursor() -> Iterator[RealDictCursor]:
    with _db_cursor() as cur:
        yield cur


def _tracer_traitement(cur: RealDictCursor, id_utilisateur: int, type_traitement: str, finalite: str, donnee_sante: bool = False) -> None:
    """Journalise un traitement (registre RGPD, art. 5.2 - accountability). Voir
    docs/rgpd/registre-traitements.md, Traitement 4."""
    cur.execute(
        "INSERT INTO traitement_rgpd (id_utilisateur, type_traitement, finalite, categorie_donnee_sante) "
        "VALUES (%s, %s, %s, %s)",
        (id_utilisateur, type_traitement, finalite, donnee_sante),
    )


@app.get("/health", tags=["monitoring"], summary="Verifie que le service est en ligne")
def health() -> dict[str, str]:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Authentification utilisateur (US1)
# ---------------------------------------------------------------------------

@app.post(
    "/auth/inscription",
    response_model=InscriptionOut,
    status_code=status.HTTP_201_CREATED,
    tags=["auth"],
    summary="Cree un compte utilisateur (US1)",
)
def inscription(payload: InscriptionIn, cur: RealDictCursor = Depends(get_cursor)) -> InscriptionOut:
    if not email_valide(payload.email):
        raise HTTPException(status_code=422, detail="Adresse email invalide")
    if not mot_de_passe_robuste(payload.mot_de_passe):
        raise HTTPException(
            status_code=422,
            detail="Le mot de passe doit contenir au moins 10 caracteres, dont une lettre et un chiffre",
        )
    # US1 : deux cases de consentement distinctes, non pre-cochees, toutes deux requises
    # (le profil allergene - donnee de sante - est une fonctionnalite centrale de l'app,
    # pas une option secondaire ; le consentement sante est donc demande des l'inscription).
    if not payload.consentement_rgpd or not payload.consentement_donnee_sante:
        raise HTTPException(status_code=422, detail="Les deux consentements RGPD sont requis pour creer un compte")

    cur.execute("SELECT 1 FROM utilisateur WHERE email = %s", (payload.email,))
    if cur.fetchone() is not None:
        raise HTTPException(status_code=409, detail="Un compte existe deja avec cet email")

    cur.execute(
        "INSERT INTO utilisateur (email, mot_de_passe_hash, consentement_rgpd, consentement_donnee_sante) "
        "VALUES (%s, %s, %s, %s) RETURNING id_utilisateur",
        (payload.email, hacher_mot_de_passe(payload.mot_de_passe), payload.consentement_rgpd, payload.consentement_donnee_sante),
    )
    id_utilisateur = cur.fetchone()["id_utilisateur"]
    _tracer_traitement(cur, id_utilisateur, "creation_compte", "Authentifier l'utilisateur")
    return InscriptionOut(id_utilisateur=id_utilisateur, email=payload.email)


@app.post(
    "/auth/connexion",
    response_model=SessionOut,
    tags=["auth"],
    summary="Authentifie un utilisateur et ouvre une session (US1)",
)
def connexion(payload: ConnexionIn, cur: RealDictCursor = Depends(get_cursor)) -> SessionOut:
    if verrouille_pour_bruteforce(payload.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trop de tentatives echouees ; reessayez dans quelques minutes",
        )

    cur.execute("SELECT id_utilisateur, mot_de_passe_hash FROM utilisateur WHERE email = %s", (payload.email,))
    ligne = cur.fetchone()
    hash_stocke = ligne["mot_de_passe_hash"] if ligne else None

    # Message et code d'erreur identiques que l'email existe ou non
    # (OWASP : pas d'enumeration de comptes) ; verifier_mot_de_passe() effectue
    # toujours un calcul bcrypt (contre un hash factice si necessaire) pour ne
    # pas non plus reveler l'existence du compte par le temps de reponse.
    if ligne is None or not verifier_mot_de_passe(payload.mot_de_passe, hash_stocke):
        enregistrer_echec_connexion(payload.email)
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    reinitialiser_echecs_connexion(payload.email)
    token = creer_jeton_session(ligne["id_utilisateur"])
    return SessionOut(access_token=token, expires_in_minutes=ACCESS_TOKEN_EXPIRE_MINUTES)


# ---------------------------------------------------------------------------
# Profil alimentaire (US2) - donnee de sante chiffree (pgcrypto)
# ---------------------------------------------------------------------------

@app.get(
    "/profil",
    response_model=list[ProfilAllergeneOut],
    tags=["profil"],
    summary="Liste le profil allergene de l'utilisateur connecte (US2)",
)
def lire_profil(
    id_utilisateur: int = Depends(utilisateur_courant),
    cur: RealDictCursor = Depends(get_cursor),
) -> list[ProfilAllergeneOut]:
    cur.execute(
        "SELECT a.libelle, pgp_sym_decrypt(ua.niveau_chiffre, %s) AS niveau, ua.date_maj "
        "FROM utilisateur_allergene ua JOIN allergene a ON a.id_allergene = ua.id_allergene "
        "WHERE ua.id_utilisateur = %s ORDER BY a.libelle",
        (_cle_chiffrement(), id_utilisateur),
    )
    return [ProfilAllergeneOut(**row) for row in cur.fetchall()]


@app.put(
    "/profil",
    response_model=list[ProfilAllergeneOut],
    tags=["profil"],
    summary="Remplace integralement le profil allergene de l'utilisateur connecte (US2)",
)
def remplacer_profil(
    profil: list[ProfilAllergeneIn],
    id_utilisateur: int = Depends(utilisateur_courant),
    cur: RealDictCursor = Depends(get_cursor),
) -> list[ProfilAllergeneOut]:
    cle = _cle_chiffrement()
    cur.execute("DELETE FROM utilisateur_allergene WHERE id_utilisateur = %s", (id_utilisateur,))
    for entree in profil:
        cur.execute("SELECT id_allergene FROM allergene WHERE libelle = %s", (entree.libelle,))
        ligne = cur.fetchone()
        if ligne is None:
            raise HTTPException(status_code=422, detail=f"Allergene inconnu du referentiel : {entree.libelle}")
        cur.execute(
            "INSERT INTO utilisateur_allergene (id_utilisateur, id_allergene, niveau_chiffre, date_maj) "
            "VALUES (%s, %s, pgp_sym_encrypt(%s, %s), now())",
            (id_utilisateur, ligne["id_allergene"], entree.niveau, cle),
        )
    _tracer_traitement(
        cur, id_utilisateur, "mise_a_jour_profil",
        "Detecter les incompatibilites entre le profil et un produit/une recette",
        donnee_sante=True,
    )
    cur.execute(
        "SELECT a.libelle, pgp_sym_decrypt(ua.niveau_chiffre, %s) AS niveau, ua.date_maj "
        "FROM utilisateur_allergene ua JOIN allergene a ON a.id_allergene = ua.id_allergene "
        "WHERE ua.id_utilisateur = %s ORDER BY a.libelle",
        (cle, id_utilisateur),
    )
    return [ProfilAllergeneOut(**row) for row in cur.fetchall()]


# ---------------------------------------------------------------------------
# Historique des analyses (US7)
# ---------------------------------------------------------------------------

@app.get(
    "/historique",
    response_model=list[HistoriqueOut],
    tags=["historique"],
    summary="Historique des analyses de l'utilisateur connecte (US7)",
)
def lire_historique(
    id_utilisateur: int = Depends(utilisateur_courant),
    cur: RealDictCursor = Depends(get_cursor),
) -> list[HistoriqueOut]:
    cur.execute(
        "SELECT id_analyse, code_barres, id_recette, statut_compatibilite, allergenes_detectes, date_analyse "
        "FROM analyse_compatibilite WHERE id_utilisateur = %s ORDER BY date_analyse DESC",
        (id_utilisateur,),
    )
    return [
        HistoriqueOut(
            **{**row, "allergenes_detectes": row["allergenes_detectes"].split(",") if row["allergenes_detectes"] else []}
        )
        for row in cur.fetchall()
    ]


@app.post(
    "/historique",
    response_model=HistoriqueOut,
    status_code=status.HTTP_201_CREATED,
    tags=["historique"],
    summary="Enregistre le resultat d'une analyse produit/recette dans l'historique (US7)",
)
def ajouter_historique(
    payload: HistoriqueIn,
    id_utilisateur: int = Depends(utilisateur_courant),
    cur: RealDictCursor = Depends(get_cursor),
) -> HistoriqueOut:
    # Contrainte du schema (chk_analyse_produit_ou_recette) : un historique ne
    # porte QUE sur un produit ou une recette, jamais les deux, jamais aucun -
    # une analyse de texte libre ne peut donc pas etre journalisee ici (pas
    # d'entite a laquelle la rattacher), limitation assumee et documentee.
    if (payload.code_barres is None) == (payload.id_recette is None):
        raise HTTPException(
            status_code=422,
            detail="Fournir exactement un identifiant : code_barres OU id_recette (pas d'historique pour un texte libre)",
        )
    cur.execute(
        "INSERT INTO analyse_compatibilite "
        "(id_utilisateur, code_barres, id_recette, statut_compatibilite, allergenes_detectes, substitutions_proposees) "
        "VALUES (%s, %s, %s, %s, %s, %s) "
        "RETURNING id_analyse, code_barres, id_recette, statut_compatibilite, allergenes_detectes, date_analyse",
        (
            id_utilisateur, payload.code_barres, payload.id_recette, payload.statut_compatibilite,
            ",".join(payload.allergenes_detectes), payload.substitutions_proposees,
        ),
    )
    row = cur.fetchone()
    return HistoriqueOut(
        **{**row, "allergenes_detectes": row["allergenes_detectes"].split(",") if row["allergenes_detectes"] else []}
    )


# ---------------------------------------------------------------------------
# Droits RGPD (US8)
# ---------------------------------------------------------------------------

@app.get(
    "/rgpd/export",
    response_model=ExportRgpdOut,
    tags=["rgpd"],
    summary="Exporte toutes les donnees personnelles de l'utilisateur connecte (US8, droit a la portabilite)",
)
def exporter_donnees(
    id_utilisateur: int = Depends(utilisateur_courant),
    cur: RealDictCursor = Depends(get_cursor),
) -> ExportRgpdOut:
    cur.execute(
        "SELECT id_utilisateur, email, date_inscription, consentement_rgpd, consentement_donnee_sante "
        "FROM utilisateur WHERE id_utilisateur = %s",
        (id_utilisateur,),
    )
    utilisateur = cur.fetchone()
    if utilisateur is None:
        raise HTTPException(status_code=404, detail="Compte introuvable")

    profil = lire_profil(id_utilisateur=id_utilisateur, cur=cur)
    historique = lire_historique(id_utilisateur=id_utilisateur, cur=cur)
    _tracer_traitement(cur, id_utilisateur, "export_donnees", "Exercice du droit a la portabilite (art. 20 RGPD)")
    return ExportRgpdOut(utilisateur=UtilisateurOut(**utilisateur), profil_allergene=profil, historique=historique)


@app.delete(
    "/rgpd/compte",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["rgpd"],
    summary="Supprime definitivement le compte et toutes les donnees associees (US8, droit a l'effacement)",
)
def supprimer_compte(
    confirmation_email: str = Query(..., description="Doit correspondre exactement a l'email du compte (double validation US8)"),
    id_utilisateur: int = Depends(utilisateur_courant),
    cur: RealDictCursor = Depends(get_cursor),
) -> None:
    cur.execute("SELECT email FROM utilisateur WHERE id_utilisateur = %s", (id_utilisateur,))
    ligne = cur.fetchone()
    if ligne is None:
        raise HTTPException(status_code=404, detail="Compte introuvable")
    if confirmation_email != ligne["email"]:
        raise HTTPException(status_code=400, detail="L'email de confirmation ne correspond pas au compte")

    # Le journal de tracabilite (traitement_rgpd) est en cascade sur
    # utilisateur (ON DELETE CASCADE) : il ne survit donc pas a la
    # suppression du compte. Limitation connue vis-a-vis de l'accountability
    # (art. 5.2 RGPD) permanente, documentee dans docs/04-bloc3-app/dev-application.md -
    # une preuve durable des traitements passes necessiterait un journal
    # d'audit hors cascade, hors perimetre de cette version.
    cur.execute("DELETE FROM utilisateur WHERE id_utilisateur = %s", (id_utilisateur,))
