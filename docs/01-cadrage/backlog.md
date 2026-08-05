# Backlog agile — NutriScan IA

Kanban tenu en markdown dans ce dépôt (accessible à toute partie prenante sans compte tiers). Peut être dupliqué dans **GitHub Projects** pour un rendu plus visuel : `github.com/<votre-repo>` → onglet **Projects** → nouveau projet → colonnes *Backlog / À faire / En cours / Fait* → une carte par user story et par tâche technique de `planning.md`, en les liant à ce fichier.

## Backlog produit (toutes les user stories)

| Story | Titre | Bloc concerné | Statut |
|---|---|---|---|
| [US1](user-stories.md#us1--inscription-et-connexion-sécurisées) | Inscription et connexion sécurisées | B3 | 📋 Backlog |
| [US2](user-stories.md#us2--définir-mon-profil-alimentaire) | Définir mon profil alimentaire | B3 | 📋 Backlog |
| [US3](user-stories.md#us3--rechercher-un-produit) | Rechercher un produit | B1/B3 | 📋 Backlog |
| [US4](user-stories.md#us4--alerte-allergènes-et-score-de-compatibilité) | Alerte allergènes et score de compatibilité | B2/B3 | 📋 Backlog |
| [US5](user-stories.md#us5--rechercher-une-recette-et-ses-substitutions) | Rechercher une recette et ses substitutions | B1/B2/B3 | 📋 Backlog |
| [US6](user-stories.md#us6--score-nutritionnel-détaillé) | Score nutritionnel détaillé | B1/B3 | 📋 Backlog |
| [US7](user-stories.md#us7--historique-de-mes-recherches-et-analyses) | Historique de mes recherches et analyses | B3 | 📋 Backlog |
| [US8](user-stories.md#us8--maîtrise-de-mes-données-personnelles-rgpd) | Maîtrise de mes données personnelles (RGPD) | B1/B3 | 📋 Backlog |
| [US9](user-stories.md#us9--transparence-en-cas-dindisponibilité) | Transparence en cas d'indisponibilité | B2/B3 | 📋 Backlog |

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

*(Sprints S5 à S13 : voir le détail semaine par semaine dans [`docs/00-pilotage/planning.md`](../00-pilotage/planning.md) ; les cartes correspondantes seront ajoutées ici au fur et à mesure, pas toutes d'avance, pour que le board reste le reflet honnête de l'avancement réel.)*

## Rituels agiles (C16)

- **Point hebdomadaire** (auto-évalué en solo) : en début de semaine, revue de la matrice de compétences et du sprint précédent ; en fin de semaine, mise à jour des statuts ci-dessus.
- **Definition of Done** d'une tâche : code versionné + testé + documenté (voir critères d'évaluation du référentiel pour chaque compétence).
- **Traçabilité** : chaque tâche terminée doit pouvoir être reliée à un commit Git et, si applicable, au critère d'évaluation qu'elle satisfait (voir `docs/00-pilotage/matrice-competences.md`).
