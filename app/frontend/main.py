"""Application complete NutriScan IA — Streamlit (Bloc 3, competence C17).

A la difference du prototype de demonstration de S6 (`frontend/prototype.py`,
toujours conserve pour la documentation C10), cette application integre un
compte utilisateur reel avec persistance : inscription/connexion (US1),
profil allergene sauvegarde en base et chiffre (US2), recherche de produits
et recettes avec alerte allergene (US3-US5), score nutritionnel detaille
(US6), historique des analyses (US7) et maitrise des donnees personnelles -
export et suppression de compte (US8). Elle appelle les trois API du systeme
en HTTP (Data, IA, backend applicatif) et ne se connecte jamais directement
a PostgreSQL, conformement a docs/01-cadrage/architecture.md.

Usage :
    docker compose up -d postgres api_data api_ia app_backend
    ollama serve  (+ modele tire, pour l'analyse IA)
    cd app
    py -m streamlit run frontend/main.py
"""
from __future__ import annotations

import os
from typing import Any, Optional

import requests
import streamlit as st
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

DATA_API_URL = os.environ.get("DATA_API_BASE_URL", "http://localhost:8010")
IA_API_URL = os.environ.get("IA_API_BASE_URL", "http://localhost:8011")
BACKEND_API_URL = os.environ.get("APP_BACKEND_BASE_URL", "http://localhost:8012")
CLIENT_ID = os.environ.get("API_CLIENT_ID", "nutriscan-app")
CLIENT_SECRET = os.environ.get("API_CLIENT_SECRET", "change-moi-en-local")

STATUT_AFFICHAGE = {
    "compatible": ("✅", "Compatible", "success"),
    "a_risque": ("⚠️", "À risque", "warning"),
    "incompatible": ("⛔", "Incompatible", "error"),
}
LIBELLE_NIVEAU = {
    "allergie": "Allergie (incompatibilité stricte)",
    "intolerance": "Intolérance",
    "preference": "Préférence (ex. végétarien)",
}


# ---------------------------------------------------------------------------
# Appels API Data / API IA (authentification "client credentials" service-a-
# service, voir data-pipeline/api_data/auth.py) - meme logique que le
# prototype S6.
# ---------------------------------------------------------------------------

def _token_service(base_url: str) -> Optional[str]:
    cle_cache = f"token::{base_url}"
    if cle_cache in st.session_state:
        return st.session_state[cle_cache]
    try:
        response = requests.post(
            f"{base_url}/auth/token",
            params={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET},
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        st.session_state[f"erreur::{base_url}"] = str(exc)
        return None
    token = response.json()["access_token"]
    st.session_state[cle_cache] = token
    return token


def _appel_service(base_url: str, methode: str, chemin: str, timeout: int = 15, **kwargs: Any) -> Any:
    token = _token_service(base_url)
    if token is None:
        st.error(f"Service indisponible ({base_url}) : {st.session_state.get(f'erreur::{base_url}', '')}")
        return None
    try:
        response = requests.request(
            methode, f"{base_url}{chemin}", headers={"Authorization": f"Bearer {token}"},
            timeout=timeout, **kwargs,
        )
        if response.status_code == 401:
            del st.session_state[f"token::{base_url}"]
            token = _token_service(base_url)
            response = requests.request(
                methode, f"{base_url}{chemin}", headers={"Authorization": f"Bearer {token}"},
                timeout=timeout, **kwargs,
            )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        st.error(f"Le service n'a pas pu répondre : {exc}")
        return None


def analyser_ia(chemin: str, **kwargs: Any) -> Any:
    with st.spinner("Analyse en cours (peut prendre jusqu'à une minute la première fois)…"):
        return _appel_service(IA_API_URL, "POST", chemin, timeout=90, **kwargs)


@st.cache_data(ttl=300)
def charger_allergenes_referentiel() -> list[dict[str, Any]]:
    return _appel_service(DATA_API_URL, "GET", "/allergenes") or []


@st.cache_data(ttl=60)
def nom_produit(code_barres: str) -> str:
    produit = _appel_service(DATA_API_URL, "GET", f"/produits/{code_barres}")
    return produit["nom"] if produit else code_barres


@st.cache_data(ttl=60)
def titre_recette(id_recette: int) -> str:
    recette = _appel_service(DATA_API_URL, "GET", f"/recettes/{id_recette}")
    return recette["titre"] if recette else str(id_recette)


@st.cache_data(ttl=300)
def nutrition_ciqual(code_ciqual: str) -> Optional[dict[str, Any]]:
    return _appel_service(DATA_API_URL, "GET", f"/nutrition/{code_ciqual}")


# ---------------------------------------------------------------------------
# Appels au backend applicatif (session utilisateur, voir app/backend/)
# ---------------------------------------------------------------------------

def _appel_backend(methode: str, chemin: str, timeout: int = 15, **kwargs: Any) -> tuple[Optional[Any], Optional[requests.Response]]:
    """Renvoie (corps_json, reponse). En cas de session expiree/invalide (401), deconnecte
    l'utilisateur (US9 : transparence en cas d'indisponibilite/d'erreur, jamais un echec silencieux)."""
    headers = {"Authorization": f"Bearer {st.session_state['session_token']}"}
    try:
        response = requests.request(methode, f"{BACKEND_API_URL}{chemin}", headers=headers, timeout=timeout, **kwargs)
    except requests.RequestException as exc:
        st.error(f"Le service applicatif n'a pas pu répondre : {exc}")
        return None, None
    if response.status_code == 401:
        st.session_state.pop("session_token", None)
        st.session_state.pop("email", None)
        st.error("Votre session a expiré. Merci de vous reconnecter.")
        st.rerun()
    if response.status_code >= 400:
        # US9 : ce cas (erreur HTTP renvoyee par le backend, ex. 500) ne
        # levait auparavant aucune alerte - un appelant recevant (None, reponse)
        # pouvait alors afficher a tort un message de type "aucune donnee"
        # plutot que de signaler une panne reelle (trouve en simulant une
        # panne, voir docs/04-bloc3-app/incident-resolution.md).
        detail = response.json().get("detail", response.text) if response.content else response.reason
        st.error(f"Le service applicatif a renvoyé une erreur : {detail}")
        return None, response
    corps = response.json() if response.content else None
    return corps, response


def est_connecte() -> bool:
    return "session_token" in st.session_state


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def page_authentification() -> None:
    st.subheader("Connexion à mon espace")
    onglet_connexion, onglet_inscription = st.tabs(["Se connecter", "Créer un compte"])

    with onglet_connexion:
        with st.form("formulaire_connexion"):
            email = st.text_input("Adresse email", key="connexion_email")
            mot_de_passe = st.text_input("Mot de passe", type="password", key="connexion_mdp")
            valide = st.form_submit_button("Se connecter")
        if valide:
            try:
                reponse = requests.post(
                    f"{BACKEND_API_URL}/auth/connexion",
                    json={"email": email, "mot_de_passe": mot_de_passe}, timeout=10,
                )
            except requests.RequestException as exc:
                st.error(f"Service indisponible : {exc}")
            else:
                if reponse.status_code == 200:
                    st.session_state["session_token"] = reponse.json()["access_token"]
                    st.session_state["email"] = email
                    st.rerun()
                elif reponse.status_code == 429:
                    st.error("Trop de tentatives échouées. Merci de réessayer dans quelques minutes.")
                else:
                    st.error("Email ou mot de passe incorrect.")

    with onglet_inscription:
        st.caption(
            "Le profil alimentaire (allergies/intolérances) est une donnée de santé "
            "(art. 9 du RGPD) : les deux consentements ci-dessous sont indépendants et obligatoires."
        )
        with st.form("formulaire_inscription"):
            email_i = st.text_input("Adresse email", key="inscription_email")
            mdp_i = st.text_input(
                "Mot de passe (10 caractères minimum, au moins une lettre et un chiffre)",
                type="password", key="inscription_mdp",
            )
            consent_rgpd = st.checkbox("J'accepte les conditions d'utilisation et la politique de confidentialité", key="consent_rgpd")
            consent_sante = st.checkbox(
                "J'accepte spécifiquement le traitement de mes données de santé (allergies/intolérances)",
                key="consent_sante",
            )
            valide_i = st.form_submit_button("Créer mon compte")
        if valide_i:
            try:
                reponse = requests.post(
                    f"{BACKEND_API_URL}/auth/inscription",
                    json={
                        "email": email_i, "mot_de_passe": mdp_i,
                        "consentement_rgpd": consent_rgpd, "consentement_donnee_sante": consent_sante,
                    },
                    timeout=10,
                )
            except requests.RequestException as exc:
                st.error(f"Service indisponible : {exc}")
            else:
                if reponse.status_code == 201:
                    st.success("Compte créé. Vous pouvez maintenant vous connecter dans l'onglet « Se connecter ».")
                else:
                    st.error(reponse.json().get("detail", "Impossible de créer le compte."))


def page_profil() -> None:
    st.subheader("Mon profil alimentaire")
    st.caption(
        "Sélectionnez les allergènes qui vous concernent, puis précisez le niveau. "
        "Le référentiel officiel (14 allergènes, règlement UE INCO 1169/2011) sert de base."
    )
    referentiel = charger_allergenes_referentiel()
    if "profil_charge" not in st.session_state:
        profil_actuel, _ = _appel_backend("GET", "/profil")
        if profil_actuel is None:
            # Protection contre la perte de donnees (US9) : si le chargement
            # echoue, ne jamais mettre en cache un profil vide - un simple
            # clic sur "Enregistrer" ecraserait alors silencieusement le
            # vrai profil sauvegarde par une liste vide. Bug reel trouve en
            # simulant une panne du backend (voir incident-resolution.md) :
            # mieux vaut bloquer la page que risquer d'effacer une donnee de
            # sante par accident.
            st.error("Impossible de charger votre profil actuel. Réessayez dans quelques instants.")
            return
        st.session_state["profil_charge"] = {ligne["libelle"]: ligne["niveau"] for ligne in profil_actuel}
    niveau_actuel = st.session_state["profil_charge"]

    # Pas de st.form ici volontairement : le radio "niveau" n'est affiche que
    # si la case correspondante est cochee, et les widgets d'un st.form ne
    # declenchent un rerun qu'a la soumission - la case a cocher resterait
    # donc sans effet visible tant que le formulaire n'est pas deja valide
    # (bug reellement observe en testant dans le navigateur avant ce correctif).
    nouveau_profil = []
    for allergene in referentiel:
        libelle = allergene["libelle"]
        coche = st.checkbox(f"J'ai une réaction à : {libelle}", value=libelle in niveau_actuel, key=f"chk_{allergene['id_allergene']}")
        if coche:
            options = list(LIBELLE_NIVEAU.keys())
            index_defaut = options.index(niveau_actuel.get(libelle, "allergie"))
            niveau = st.radio(
                f"Niveau pour {libelle}", options, index=index_defaut,
                format_func=lambda n: LIBELLE_NIVEAU[n], key=f"niveau_{allergene['id_allergene']}", horizontal=True,
            )
            nouveau_profil.append({"libelle": libelle, "niveau": niveau})

    if st.button("Enregistrer mon profil"):
        _, reponse = _appel_backend("PUT", "/profil", json=nouveau_profil)
        if reponse is not None and reponse.status_code == 200:
            st.session_state.pop("profil_charge", None)
            st.success("Profil enregistré.")
            st.rerun()
        elif reponse is not None:
            st.error(reponse.json().get("detail", "Échec de l'enregistrement du profil."))


def _profil_pour_analyse() -> list[dict[str, str]]:
    profil, _ = _appel_backend("GET", "/profil")
    return [{"libelle": p["libelle"], "niveau": p["niveau"]} for p in (profil or [])]


def afficher_resultat(resultat: dict[str, Any]) -> None:
    if not resultat.get("ia_disponible", True):
        # US9 : ne jamais laisser croire a une analyse complete quand le
        # modele IA est indisponible - le resultat repose alors uniquement
        # sur le filet de securite par mots-cles (voir extraction.py,
        # incident simule en S11 : docs/04-bloc3-app/incident-resolution.md).
        st.warning("⚠️ Service IA temporairement indisponible : analyse basée uniquement sur la recherche de mots-clés, moins fiable.")

    icone, libelle, niveau = STATUT_AFFICHAGE[resultat["statut_compatibilite"]]
    getattr(st, niveau)(f"{icone} **{libelle}**")

    if resultat["allergenes_problematiques"]:
        st.markdown("**Allergènes posant problème avec votre profil :** " + ", ".join(resultat["allergenes_problematiques"]))
    if resultat["allergenes_detectes"]:
        st.markdown("**Tous les allergènes détectés :** " + ", ".join(resultat["allergenes_detectes"]))
    else:
        st.markdown("Aucun allergène détecté dans ce texte.")

    with st.expander("Détail de la détection (transparence de l'analyse)"):
        st.markdown(f"- Détectés par l'IA : {', '.join(resultat['detection_ia']) or 'aucun'}")
        st.markdown(f"- Détectés par recherche de mots-clés (filet de sécurité) : {', '.join(resultat['detection_mots_cles']) or 'aucun'}")
        if resultat["justification_ia"]:
            st.markdown(f"- Justification du modèle : _{resultat['justification_ia']}_")


def afficher_score_nutritionnel_produit(produit_detail: dict[str, Any]) -> None:
    champs = [
        ("Énergie", produit_detail.get("energie_kcal_100g"), "kcal/100g"),
        ("Protéines", produit_detail.get("proteines_g_100g"), "g/100g"),
        ("Glucides", produit_detail.get("glucides_g_100g"), "g/100g"),
        ("Lipides", produit_detail.get("lipides_g_100g"), "g/100g"),
    ]
    if all(valeur is None for _, valeur, _ in champs):
        st.caption("Valeurs nutritionnelles détaillées non disponibles pour ce produit (au-delà du Nutri-Score).")
        return
    st.markdown("**Score nutritionnel détaillé** _(source : Open Food Facts, pour 100g/100ml)_")
    st.table({nom: f"{valeur:.1f} {unite}" if valeur is not None else "non renseigné" for nom, valeur, unite in champs})


def afficher_score_nutritionnel_recette(ingredients: list[dict[str, Any]]) -> None:
    lies = [i for i in ingredients if i.get("code_ciqual")]
    if not lies:
        st.caption("Aucun ingrédient de cette recette n'a pu être rapproché de la table Ciqual.")
        return
    totaux = {"energie_kcal": 0.0, "proteines_g": 0.0, "glucides_g": 0.0, "lipides_g": 0.0}
    trouves = 0
    for ingredient in lies:
        donnees = nutrition_ciqual(ingredient["code_ciqual"])
        if donnees is None:
            continue
        trouves += 1
        totaux["energie_kcal"] += donnees.get("energie_kcal") or 0
        totaux["proteines_g"] += donnees.get("proteines_g") or 0
        totaux["glucides_g"] += donnees.get("glucides_g") or 0
        totaux["lipides_g"] += donnees.get("lipides_g") or 0
    st.markdown(
        f"**Score nutritionnel (approximatif)** _(source : table Ciqual/ANSES, "
        f"{trouves}/{len(ingredients)} ingrédients reconnus — somme non pondérée par les quantités)_"
    )
    st.table({
        "Énergie (somme)": f"{totaux['energie_kcal']:.0f} kcal",
        "Protéines (somme)": f"{totaux['proteines_g']:.1f} g",
        "Glucides (somme)": f"{totaux['glucides_g']:.1f} g",
        "Lipides (somme)": f"{totaux['lipides_g']:.1f} g",
    })


def _enregistrer_historique(**kwargs: Any) -> None:
    _, reponse = _appel_backend("POST", "/historique", json=kwargs)
    if reponse is not None and reponse.status_code == 201:
        st.caption("📌 Analyse ajoutée à votre historique.")


def page_recherche_produit() -> None:
    st.subheader("Rechercher un produit")
    recherche = st.text_input("Filtrer par catégorie (ex. « biscuit »)", key="recherche_produit")
    produits = _appel_service(DATA_API_URL, "GET", "/produits", params={"categorie": recherche, "limit": 20})
    # US9 : ne jamais confondre "service indisponible" (erreur deja affichee par
    # _appel_service, produits vaut None) et "recherche sans resultat" (liste
    # vide valide) - bug reel trouve lors de la simulation d'incident (panne de
    # l'API Data), voir docs/04-bloc3-app/incident-resolution.md.
    if produits is None:
        return
    if not produits:
        st.info("Aucun produit trouvé pour ce filtre.")
        return
    options = {f"{p['nom']} ({p['code_barres']})": p["code_barres"] for p in produits}
    choix = st.selectbox("Produit", list(options.keys()))
    code_barres = options[choix]
    if st.button("Analyser ce produit"):
        resultat = analyser_ia(f"/analyser/produit/{code_barres}", json={"allergies_utilisateur": _profil_pour_analyse()})
        if resultat is None:
            st.error("Produit introuvable ou service indisponible.")
            return
        afficher_resultat(resultat)
        detail = _appel_service(DATA_API_URL, "GET", f"/produits/{code_barres}")
        if detail:
            afficher_score_nutritionnel_produit(detail)
        _enregistrer_historique(
            code_barres=code_barres, statut_compatibilite=resultat["statut_compatibilite"],
            allergenes_detectes=resultat["allergenes_detectes"],
        )


def page_recherche_recette() -> None:
    st.subheader("Rechercher une recette")
    recettes = _appel_service(DATA_API_URL, "GET", "/recettes", params={"limit": 20})
    # US9 : voir le commentaire equivalent de page_recherche_produit.
    if recettes is None:
        return
    if not recettes:
        st.info("Aucune recette disponible.")
        return
    options = {r["titre"]: r["id_recette"] for r in recettes}
    choix = st.selectbox("Recette", list(options.keys()))
    id_recette = options[choix]
    if st.button("Analyser cette recette"):
        resultat = analyser_ia(f"/analyser/recette/{id_recette}", json={"allergies_utilisateur": _profil_pour_analyse()})
        if resultat is None:
            st.error("Recette introuvable ou service indisponible.")
            return
        afficher_resultat(resultat)
        detail = _appel_service(DATA_API_URL, "GET", f"/recettes/{id_recette}")
        if detail:
            afficher_score_nutritionnel_recette(detail["ingredients"])
        _enregistrer_historique(
            id_recette=id_recette, statut_compatibilite=resultat["statut_compatibilite"],
            allergenes_detectes=resultat["allergenes_detectes"],
        )


def page_texte_libre() -> None:
    st.subheader("Analyser un texte libre")
    st.caption("Ex. une liste d'ingrédients recopiée d'une étiquette. Ce type d'analyse n'est pas conservé dans l'historique (aucun produit/recette catalogué associé).")
    texte = st.text_area("Liste d'ingrédients", height=120, key="texte_libre")
    if st.button("Analyser ce texte") and texte.strip():
        resultat = analyser_ia("/analyser/texte", json={"texte": texte, "allergies_utilisateur": _profil_pour_analyse()})
        if resultat is not None:
            afficher_resultat(resultat)


def page_historique() -> None:
    st.subheader("Mon historique d'analyses")
    historique, _ = _appel_backend("GET", "/historique")
    # US9 : voir le commentaire equivalent de page_recherche_produit - un
    # service indisponible (erreur deja affichee par _appel_backend) ne doit
    # jamais etre confondu avec un historique reellement vide.
    if historique is None:
        return
    if not historique:
        st.info("Aucune analyse enregistrée pour l'instant.")
        return
    lignes = []
    for entree in historique:
        icone, libelle_statut, _ = STATUT_AFFICHAGE[entree["statut_compatibilite"]]
        nom = nom_produit(entree["code_barres"]) if entree["code_barres"] else titre_recette(entree["id_recette"])
        lignes.append({
            "Date": entree["date_analyse"][:16].replace("T", " "),
            "Produit / recette": nom,
            "Résultat": f"{icone} {libelle_statut}",
            "Allergènes détectés": ", ".join(entree["allergenes_detectes"]) or "aucun",
        })
    st.table(lignes)


def page_rgpd() -> None:
    st.subheader("Mes données personnelles (RGPD)")

    st.markdown("#### Exporter mes données")
    st.caption("Droit à la portabilité (art. 20 RGPD) : télécharge votre compte, votre profil et votre historique au format JSON.")
    if st.button("Préparer mon export"):
        export, reponse = _appel_backend("GET", "/rgpd/export")
        if export is not None:
            import json
            st.download_button(
                "Télécharger mes données (JSON)", data=json.dumps(export, ensure_ascii=False, indent=2),
                file_name="nutriscan_mes_donnees.json", mime="application/json",
            )

    st.divider()
    st.markdown("#### Supprimer définitivement mon compte")
    st.warning(
        "⚠️ Action irréversible : votre compte, votre profil allergène et votre historique "
        "seront définitivement supprimés."
    )
    confirmation = st.text_input(f"Retapez votre email ({st.session_state.get('email', '')}) pour confirmer", key="confirmation_suppression")
    comprend = st.checkbox("Je comprends que cette action est irréversible", key="comprend_suppression")
    if st.button("Supprimer définitivement mon compte", disabled=not comprend):
        if confirmation != st.session_state.get("email"):
            st.error("L'email saisi ne correspond pas à votre compte.")
        else:
            _, reponse = _appel_backend("DELETE", "/rgpd/compte", params={"confirmation_email": confirmation})
            if reponse is not None and reponse.status_code == 204:
                st.session_state.clear()
                st.session_state["message_deconnexion"] = "Votre compte a été supprimé."
                st.rerun()
            elif reponse is not None:
                st.error(reponse.json().get("detail", "Échec de la suppression du compte."))


def main() -> None:
    st.set_page_config(page_title="NutriScan IA", page_icon="🥗", layout="centered")
    st.title("🥗 NutriScan IA")
    st.warning(
        "⚠️ Cet outil est une aide à la lecture d'étiquettes et de recettes. "
        "Il ne constitue en aucun cas un avis médical."
    )

    if "message_deconnexion" in st.session_state:
        st.success(st.session_state.pop("message_deconnexion"))

    if not est_connecte():
        page_authentification()
        return

    st.sidebar.markdown(f"Connecté : **{st.session_state.get('email', '')}**")
    if st.sidebar.button("Se déconnecter"):
        st.session_state.clear()
        st.session_state["message_deconnexion"] = "Vous avez été déconnecté."
        st.rerun()

    page = st.sidebar.radio(
        "Navigation",
        ["Mon profil", "Rechercher un produit", "Rechercher une recette", "Texte libre", "Historique", "Mes données (RGPD)"],
    )
    st.divider()

    {
        "Mon profil": page_profil,
        "Rechercher un produit": page_recherche_produit,
        "Rechercher une recette": page_recherche_recette,
        "Texte libre": page_texte_libre,
        "Historique": page_historique,
        "Mes données (RGPD)": page_rgpd,
    }[page]()


if __name__ == "__main__":
    main()
