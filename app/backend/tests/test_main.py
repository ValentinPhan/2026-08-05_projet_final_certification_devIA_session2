"""Tests d'integration du backend applicatif (C17), contre la vraie base PostgreSQL.

Contrairement aux tests unitaires de securite (test_security.py, purs, sans
IO), ces tests exercent le vrai cycle SQL (dont le chiffrement pgcrypto du
profil allergene) : ils necessitent Postgres demarre et le schema applique
(voir data-pipeline/db/schema.sql, docker-compose.yml), exactement comme
app/tests/test_integration.py pour le reste de la stack. Ignores
automatiquement si la base n'est pas joignable.

Chaque test cree son propre utilisateur avec un email unique (horodatage) et
le supprime a la fin (fixture `compte`), pour rester rejouable sans polluer
la base au fil des executions.

Usage :
    docker compose up -d postgres
    cd app
    py -m pytest backend/tests/test_main.py -v
"""
from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from backend.common.db import get_connection
from backend.main import app

client = TestClient(app)


def _db_disponible() -> bool:
    try:
        get_connection().close()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _db_disponible(), reason="PostgreSQL non demarre : `docker compose up -d postgres`")


def _email_unique(prefix: str) -> str:
    return f"{prefix}.{time.time_ns()}@example.com"


@pytest.fixture
def code_barres_existant() -> str:
    """Un vrai code-barres present en base : `analyse_compatibilite.code_barres` a une
    contrainte de cle etrangere vers `produit`, un code invente violerait cette contrainte
    (comme decouvert en executant ces tests pour de vrai contre la base reelle)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT code_barres FROM produit LIMIT 1")
            ligne = cur.fetchone()
    finally:
        conn.close()
    if ligne is None:
        pytest.skip("Aucun produit en base : executer data-pipeline/load/import_data.py au prealable")
    return ligne[0]


@pytest.fixture
def compte():
    """Cree un compte de test, fournit (email, mot_de_passe, token), le supprime a la fin."""
    email = _email_unique("test-backend")
    mot_de_passe = "MotDePasse123"
    reponse = client.post("/auth/inscription", json={
        "email": email, "mot_de_passe": mot_de_passe,
        "consentement_rgpd": True, "consentement_donnee_sante": True,
    })
    assert reponse.status_code == 201
    token = client.post("/auth/connexion", json={"email": email, "mot_de_passe": mot_de_passe}).json()["access_token"]
    yield {"email": email, "mot_de_passe": mot_de_passe, "token": token}
    client.delete("/rgpd/compte", params={"confirmation_email": email}, headers={"Authorization": f"Bearer {token}"})


def test_health_sans_authentification():
    reponse = client.get("/health")
    assert reponse.status_code == 200


def test_inscription_rejette_email_deja_utilise(compte):
    reponse = client.post("/auth/inscription", json={
        "email": compte["email"], "mot_de_passe": "AutreMotDePasse123",
        "consentement_rgpd": True, "consentement_donnee_sante": True,
    })
    assert reponse.status_code == 409


def test_inscription_rejette_mot_de_passe_faible():
    reponse = client.post("/auth/inscription", json={
        "email": _email_unique("test-faible"), "mot_de_passe": "trop court",
        "consentement_rgpd": True, "consentement_donnee_sante": True,
    })
    assert reponse.status_code == 422


def test_inscription_rejette_consentement_manquant():
    reponse = client.post("/auth/inscription", json={
        "email": _email_unique("test-consentement"), "mot_de_passe": "MotDePasse123",
        "consentement_rgpd": True, "consentement_donnee_sante": False,
    })
    assert reponse.status_code == 422


def test_connexion_avec_mauvais_mot_de_passe_renvoie_401_generique(compte):
    reponse = client.post("/auth/connexion", json={"email": compte["email"], "mot_de_passe": "mauvais-mdp"})
    assert reponse.status_code == 401


def test_connexion_email_inconnu_renvoie_le_meme_401(compte):
    """Meme code d'erreur qu'un mauvais mot de passe : pas d'enumeration de comptes (OWASP)."""
    reponse_mdp = client.post("/auth/connexion", json={"email": compte["email"], "mot_de_passe": "mauvais"})
    reponse_email = client.post("/auth/connexion", json={"email": "personne@example.com", "mot_de_passe": "mauvais"})
    assert reponse_mdp.status_code == reponse_email.status_code == 401


def test_profil_vide_par_defaut(compte):
    reponse = client.get("/profil", headers={"Authorization": f"Bearer {compte['token']}"})
    assert reponse.status_code == 200
    assert reponse.json() == []


def test_profil_sans_jeton_refuse():
    reponse = client.get("/profil")
    assert reponse.status_code in (401, 403)


def test_maj_profil_puis_lecture_roundtrip(compte):
    headers = {"Authorization": f"Bearer {compte['token']}"}
    corps = [{"libelle": "Lait", "niveau": "allergie"}, {"libelle": "Soja", "niveau": "preference"}]
    reponse = client.put("/profil", json=corps, headers=headers)
    assert reponse.status_code == 200
    libelles = {ligne["libelle"]: ligne["niveau"] for ligne in reponse.json()}
    assert libelles == {"Lait": "allergie", "Soja": "preference"}

    relecture = client.get("/profil", headers=headers).json()
    assert {ligne["libelle"]: ligne["niveau"] for ligne in relecture} == libelles


def test_maj_profil_rejette_un_allergene_inconnu(compte):
    headers = {"Authorization": f"Bearer {compte['token']}"}
    reponse = client.put("/profil", json=[{"libelle": "Allergene inexistant", "niveau": "allergie"}], headers=headers)
    assert reponse.status_code == 422


def test_historique_vide_par_defaut(compte):
    reponse = client.get("/historique", headers={"Authorization": f"Bearer {compte['token']}"})
    assert reponse.status_code == 200
    assert reponse.json() == []


def test_ajout_historique_puis_lecture(compte, code_barres_existant):
    headers = {"Authorization": f"Bearer {compte['token']}"}
    corps = {"code_barres": code_barres_existant, "statut_compatibilite": "a_risque", "allergenes_detectes": ["Lait"]}
    reponse = client.post("/historique", json=corps, headers=headers)
    assert reponse.status_code == 201
    assert reponse.json()["allergenes_detectes"] == ["Lait"]

    historique = client.get("/historique", headers=headers).json()
    assert len(historique) == 1
    assert historique[0]["code_barres"] == code_barres_existant


def test_ajout_historique_rejette_produit_et_recette_simultanes(compte):
    headers = {"Authorization": f"Bearer {compte['token']}"}
    corps = {"code_barres": "123", "id_recette": 1, "statut_compatibilite": "compatible"}
    reponse = client.post("/historique", json=corps, headers=headers)
    assert reponse.status_code == 422


def test_export_rgpd_contient_profil_et_historique(compte, code_barres_existant):
    headers = {"Authorization": f"Bearer {compte['token']}"}
    client.put("/profil", json=[{"libelle": "Arachides", "niveau": "allergie"}], headers=headers)
    client.post("/historique", json={"code_barres": code_barres_existant, "statut_compatibilite": "compatible"}, headers=headers)

    export = client.get("/rgpd/export", headers=headers)
    assert export.status_code == 200
    corps = export.json()
    assert corps["utilisateur"]["email"] == compte["email"]
    assert len(corps["profil_allergene"]) == 1
    assert len(corps["historique"]) == 1


def test_suppression_compte_rejette_mauvaise_confirmation(compte):
    headers = {"Authorization": f"Bearer {compte['token']}"}
    reponse = client.delete("/rgpd/compte", params={"confirmation_email": "mauvais@example.com"}, headers=headers)
    assert reponse.status_code == 400


def test_suppression_compte_puis_connexion_impossible():
    email = _email_unique("test-suppression")
    mot_de_passe = "MotDePasse123"
    client.post("/auth/inscription", json={
        "email": email, "mot_de_passe": mot_de_passe,
        "consentement_rgpd": True, "consentement_donnee_sante": True,
    })
    token = client.post("/auth/connexion", json={"email": email, "mot_de_passe": mot_de_passe}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    reponse = client.delete("/rgpd/compte", params={"confirmation_email": email}, headers=headers)
    assert reponse.status_code == 204

    reponse_connexion = client.post("/auth/connexion", json={"email": email, "mot_de_passe": mot_de_passe})
    assert reponse_connexion.status_code == 401


def test_limite_de_debit_sur_connexion_declenchee():
    from backend.security import RATE_LIMIT_MAX_TENTATIVES

    email = _email_unique("test-bruteforce")
    for _ in range(RATE_LIMIT_MAX_TENTATIVES):
        reponse = client.post("/auth/connexion", json={"email": email, "mot_de_passe": "mauvais"})
        assert reponse.status_code == 401
    derniere = client.post("/auth/connexion", json={"email": email, "mot_de_passe": "mauvais"})
    assert derniere.status_code == 429
