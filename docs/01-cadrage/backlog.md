# Backlog agile — NutriScan IA

Kanban tenu en markdown dans ce dépôt (accessible à toute partie prenante sans compte tiers). Peut être dupliqué dans **GitHub Projects** pour un rendu plus visuel : `github.com/<votre-repo>` → onglet **Projects** → nouveau projet → colonnes *Backlog / À faire / En cours / Fait* → une carte par user story et par tâche technique de `planning.md`, en les liant à ce fichier.

## Backlog produit (toutes les user stories)

| Story | Titre | Bloc concerné | Statut |
|---|---|---|---|
| [US1](user-stories.md#us1--inscription-et-connexion-sécurisées) | Inscription et connexion sécurisées | B3 | ✅ Fait |
| [US2](user-stories.md#us2--définir-mon-profil-alimentaire) | Définir mon profil alimentaire | B3 | ✅ Fait |
| [US3](user-stories.md#us3--rechercher-un-produit) | Rechercher un produit | B1/B3 | ✅ Fait |
| [US4](user-stories.md#us4--alerte-allergènes-et-score-de-compatibilité) | Alerte allergènes et score de compatibilité | B2/B3 | ✅ Fait |
| [US5](user-stories.md#us5--rechercher-une-recette-et-ses-substitutions) | Rechercher une recette et ses substitutions | B1/B2/B3 | 🚧 Recherche + analyse faites, substitutions restantes |
| [US6](user-stories.md#us6--score-nutritionnel-détaillé) | Score nutritionnel détaillé | B1/B3 | ✅ Fait |
| [US7](user-stories.md#us7--historique-de-mes-recherches-et-analyses) | Historique de mes recherches et analyses | B3 | ✅ Fait |
| [US8](user-stories.md#us8--maîtrise-de-mes-données-personnelles-rgpd) | Maîtrise de mes données personnelles (RGPD) | B1/B3 | ✅ Fait |
| [US9](user-stories.md#us9--transparence-en-cas-dindisponibilité) | Transparence en cas d'indisponibilité | B2/B3 | ✅ Fait |

Statuts possibles : 📋 Backlog · 🔜 À faire (sprint courant) · 🚧 En cours · ✅ Fait

## Board par sprint

### Sprint S1 — Cadrage (17→21/03) — ✅ Fait
- [x] Cahier des charges (`cahier-des-charges.md`)
- [x] User stories + parcours utilisateur (`user-stories.md`)
- [x] MCD/MLD Merise (`merise.md`)
- [x] Architecture technique (`architecture.md`)
- [x] Mise en place du backlog agile (ce fichier)

### Sprint S2 — Collecte de données (24→28/03) — ✅ Fait
- [x] Script d'appel à l'API Open Food Facts (`extract/openfoodfacts_api.py`)
- [x] Script de scraping d'une source de recettes (`extract/scrape_recettes.py`)
- [x] Chargement du fichier Ciqual (ANSES) (`extract/ciqual_loader.py`)
- [x] Requête DuckDB sur l'export complet Open Food Facts (`extract/duckdb_openfoodfacts.py`)
- [x] Script d'agrégation / nettoyage multi-sources (`transform/clean_aggregate.py`)
- [x] Documentation C1/C2/C3 (`docs/02-bloc1-data/`)

### Sprint S3 — BDD + API Data (31/03→04/04) — ✅ Fait
- [x] Schéma PostgreSQL (MLD), y compris chiffrement pgcrypto de la table des allergies
- [x] Environnement Docker Compose (postgres + api_data)
- [x] Script d'import des données
- [x] Registre des traitements RGPD (avec focus donnée de santé)
- [x] API REST Data (FastAPI) + doc Swagger

### Sprint S4 — Veille + benchmark IA (07→11/04) — ✅ Fait
- [x] Script d'agrégation de veille (`ai-service/veille/aggregate_veille.py`, 4 flux RSS/Atom sans compte)
- [x] Synthèse de veille technique et réglementaire (`docs/03-bloc2-ia/veille.md`)
- [x] Benchmark des services IA (`docs/03-bloc2-ia/benchmark-services-ia.md`) — Ollama retenu

### Sprint S5 — POC service IA (14→18/04) — ✅ Fait
- [x] Installation/démarrage d'Ollama, récupération du modèle `llama3.2:3b`
- [x] Client API Data réutilisable (`ai-service/common/data_api_client.py`)
- [x] Script de POC (`ai-service/poc/extraction_poc.py`) testé sur 10 produits réels
- [x] Documentation du POC, limites honnêtes et recommandation pour S6 (`docs/03-bloc2-ia/poc.md`)

### Sprint S6 — API IA + prototype (21→25/04) — ✅ Fait
- [x] Détection hybride IA + mots-clés (`ai-service/api_ia/extraction.py`)
- [x] API REST IA avec auth JWT et limitation de débit (`ai-service/api_ia/`)
- [x] 19 tests unitaires (auth, endpoints, statut de compatibilité)
- [x] Conteneurisation + vérification avec Ollama réel (`docker-compose.yml`)
- [x] Prototype Streamlit (`app/frontend/prototype.py`), testé dans un navigateur
- [x] 9 tests d'intégration bout-en-bout (`app/tests/test_integration.py`)
- [x] 2 bugs réels trouvés et corrigés en testant (timeout, angle mort multilingue) — voir `docs/03-bloc2-ia/prototype.md`

### Sprint S7 — Monitoring modèle + tests (28/04→02/05) — ✅ Fait
- [x] Golden dataset de reference (`ai-service/common/golden_dataset.py`, 11 cas reels)
- [x] 4 bugs reels corriges grace au golden dataset (anglais manquant, "farine"/"beurre"/"noix" trop generiques, ligature "œ" non normalisee)
- [x] Tests automatises du modele a 3 niveaux (`ai-service/api_ia/tests/test_modele_qualite.py`)
- [x] Monitoring MLflow (`ai-service/monitoring/evaluer_modele.py`), tableau de bord verifie dans un navigateur
- [x] Decouverte via le monitoring : biais de sur-detection du gluten du modele local, documente avec recommandations
- [x] `docs/03-bloc2-ia/monitoring-modele.md` et `tests-modele.md`

### Sprint S8 — CI/CD MLOps (05→09/05) — ✅ Fait
- [x] Workflow GitHub Actions a 3 etapes (`.github/workflows/mlops-ci-cd.yml`) : tests donnees -> evaluation modele (Ollama reel, MLflow) -> packaging (GHCR)
- [x] Bug de syntaxe YAML reel trouve et corrige via `act`
- [x] Mecanique du conteneur de service Ollama et de l'API `/api/pull` verifiees en conditions reelles
- [x] `docs/03-bloc2-ia/cicd-mlops.md`
- [x] **Bloc 2 (E2+E3) complet : C6 a C13 tous valides**

### Sprint S9 — Application complète (12→16/05) — ✅ Fait
- [x] Backend applicatif FastAPI (`app/backend/`) : inscription/connexion, profil chiffré (pgcrypto), historique, export/suppression RGPD
- [x] Bug réel corrigé : `passlib` incompatible avec `bcrypt` recent (remplacé par un usage direct de `bcrypt`)
- [x] 33 tests automatisés (14 unitaires securite + 19 d'integration contre la vraie base)
- [x] Application Streamlit complète (`app/frontend/main.py`) : profil, recherche produit/recette, texte libre, historique, RGPD
- [x] Bug réel corrigé : sélecteur de niveau invisible dans un `st.form` (widgets sortis du formulaire)
- [x] Enrichissement Bloc 1 nécessaire à US6 : nutriments produits (Open Food Facts) persistés, raprochement ingrédient-Ciqual (80 % de couverture réelle)
- [x] Vérification complète dans le navigateur : inscription → profil → analyse produit/recette (Ollama réel) → historique → export/suppression RGPD
- [x] `docs/04-bloc3-app/dev-application.md`
- [x] **C17 valide**

### Sprint S10 — CI/CD Application (19→23/05) — ✅ Fait
- [x] Workflow CI applicatif (`.github/workflows/ci-app.yml`) : lint (ruff) + tests backend contre un vrai service container PostgreSQL
- [x] Decision documentee : pas d'hebergement pre-prod chez un tiers (aurait exige un compte externe) - la CD publie des images Docker versionnees sur GHCR (voir `architecture.md`, §7)
- [x] Dockerfile du frontend Streamlit (jusque-la execute hors conteneur)
- [x] Workflow CD applicatif (`.github/workflows/cd-app.yml`) : publication backend + frontend sur GHCR, declenchee uniquement apres succes de la CI (`workflow_run`)
- [x] Bug reel corrige : Starlette 1.x exige le paquet `httpx2` pour `TestClient`, absent de `backend/requirements.txt`
- [x] Verifie en conditions reelles sur GitHub Actions : run CI #1 echoue (bug ci-dessus), run #2 reussi (43s) ; run CD #1 correctement `skipped` (CI en echec), run CD #2 reussi (1m24s), images confirmees sur la page Packages du compte GitHub
- [x] `docs/04-bloc3-app/ci.md` et `cd.md`
- [x] **C18 et C19 valides**

### Sprint S11 — Monitoring app + incident (26→30/05) — ✅ Fait
- [x] Deux incidents réellement simulés (arrêt effectif des conteneurs/processus) : panne de l'API Data, panne d'Ollama
- [x] 4 bugs réels trouvés et corrigés côté frontend (confusion panne/résultat vide sur 3 pages, risque de perte du profil allergène en cas de panne)
- [x] Bug critique corrigé côté service IA (`ai-service/api_ia/extraction.py`) : une panne d'Ollama faisait échouer toute l'analyse au lieu de degrader sur le filet de sécurité par mots-clés — touche le Bloc 2, assumé car découvert en exploitant réellement l'application (Bloc 3)
- [x] US9 (transparence en cas d'indisponibilité) close par ces deux incidents
- [x] Journalisation structurée JSON (`app/backend/common/logging_config.py`), sans aucune donnée de santé ni secret en clair
- [x] Métriques Prometheus (`GET /metrics`) + tableau de bord Grafana provisionné automatiquement (`app/monitoring/`)
- [x] Bug réel corrigé : `grafana/grafana:latest` resolu vers une version au rendu casse - epingle a `11.1.0`
- [x] `docs/04-bloc3-app/monitoring-app.md` et `incident-resolution.md`
- [x] **C20 et C21 valides — Bloc 3 (C14 à C21) complet**

*(Sprints S12-S13 : voir le détail semaine par semaine dans [`docs/00-pilotage/planning.md`](../00-pilotage/planning.md) ; les cartes correspondantes seront ajoutées ici au fur et à mesure, pas toutes d'avance, pour que le board reste le reflet honnête de l'avancement réel.)*

## Rituels agiles (C16)

- **Point hebdomadaire** (auto-évalué en solo) : en début de semaine, revue de la matrice de compétences et du sprint précédent ; en fin de semaine, mise à jour des statuts ci-dessus.
- **Definition of Done** d'une tâche : code versionné + testé + documenté (voir critères d'évaluation du référentiel pour chaque compétence).
- **Traçabilité** : chaque tâche terminée doit pouvoir être reliée à un commit Git et, si applicable, au critère d'évaluation qu'elle satisfait (voir `docs/00-pilotage/matrice-competences.md`).
