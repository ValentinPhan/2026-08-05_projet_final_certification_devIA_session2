# Matrice de traçabilité des compétences — NutriScan IA

Cette matrice relie chaque compétence du référentiel RNCP (`Référentiel Dev IA Lyon P6.xlsx`) au livrable prévu dans ce dépôt. Elle sert d'auto-contrôle de conformité tout au long du projet et de sommaire pour le jury.

**Les 21 compétences sont couvertes et documentées.** Synthèse par épreuve, avec analyse réflexive, dans les [rapports professionnels](../05-rapports-professionnels/README.md) (S12).

Statuts : ⏳ à faire · 🚧 en cours · ✅ fait et documenté

## Bloc 1 — E1 (S2-S3)

Rapport : [`e1-bloc1-donnees.md`](../05-rapports-professionnels/e1-bloc1-donnees.md)

| Code | Compétence (résumé) | Semaine | Livrable prévu | Statut |
|---|---|---|---|---|
| C1 | Automatiser l'extraction de données (API, scraping, fichier, BDD, big data) | S2 | `data-pipeline/extract/` (Open Food Facts, scraping recettes, fichier Ciqual, dump OFF via DuckDB), `docs/02-bloc1-data/extraction.md` | ✅ |
| C2 | Développer des requêtes SQL d'extraction | S2 | `data-pipeline/extract/duckdb_openfoodfacts.py`, `docs/02-bloc1-data/requetes-sql.md` | ✅ (partiel — requêtes d'import SQL restantes en S3) |
| C3 | Développer des règles d'agrégation de données multi-sources | S2 | `data-pipeline/transform/`, `docs/02-bloc1-data/agregation.md` | ✅ |
| C4 | Créer une base de données conforme RGPD (Merise) | S3 | `data-pipeline/db/schema.sql`, `docs/rgpd/` | ✅ |
| C5 | Développer une API REST Data | S3 | `data-pipeline/api_data/`, `docs/02-bloc1-data/api-data.md` | ✅ |

## Bloc 2 — E2 (S4-S5) + E3 (S6-S8)

Rapports : [`e2-bloc2-veille-benchmark-poc.md`](../05-rapports-professionnels/e2-bloc2-veille-benchmark-poc.md) (E2) · [`e3-bloc2-api-ia-monitoring-cicd.md`](../05-rapports-professionnels/e3-bloc2-api-ia-monitoring-cicd.md) (E3)

| Code | Compétence (résumé) | Semaine | Livrable prévu | Statut |
|---|---|---|---|---|
| C6 | Organiser et réaliser une veille technique et réglementaire | S4 | `ai-service/veille/`, `docs/03-bloc2-ia/veille.md` | ✅ |
| C7 | Identifier des services IA préexistants (benchmark) | S4 | `docs/03-bloc2-ia/benchmark-services-ia.md` | ✅ |
| C8 | Paramétrer un service IA (POC Ollama local) | S5 | `ai-service/poc/`, `docs/03-bloc2-ia/poc.md` | ✅ |
| C9 | Développer une API REST exposant un modèle/service IA | S6 | `ai-service/api_ia/`, `docs/03-bloc2-ia/api-ia.md` | ✅ |
| C10 | Intégrer l'API IA dans une application prototype | S6 | `app/frontend/prototype.py`, `docs/03-bloc2-ia/prototype.md` | ✅ |
| C11 | Monitorer un modèle IA | S7 | `ai-service/monitoring/`, `docs/03-bloc2-ia/monitoring-modele.md` | ✅ |
| C12 | Programmer les tests automatisés du modèle IA | S7 | `ai-service/api_ia/tests/test_modele_qualite.py`, `docs/03-bloc2-ia/tests-modele.md` | ✅ |
| C13 | Créer une chaîne CI/CD MLOps | S8 | `.github/workflows/mlops-ci-cd.yml`, `docs/03-bloc2-ia/cicd-mlops.md` | ✅ |

## Bloc 3 — E4 (S1, S9-S10) + E5 (S11)

Rapports : [`e4-bloc3-cadrage-application-cicd.md`](../05-rapports-professionnels/e4-bloc3-cadrage-application-cicd.md) (E4) · [`e5-bloc3-monitoring-incidents.md`](../05-rapports-professionnels/e5-bloc3-monitoring-incidents.md) (E5)

| Code | Compétence (résumé) | Semaine | Livrable prévu | Statut |
|---|---|---|---|---|
| C14 | Analyser le besoin d'application IA (specs, modélisation, accessibilité) | S1 | `docs/01-cadrage/cahier-des-charges.md`, `docs/01-cadrage/user-stories.md` | ✅ |
| C15 | Concevoir le cadre technique de l'application | S1 | `docs/01-cadrage/architecture.md` | ✅ |
| C16 | Coordonner la réalisation technique (agilité/MLOps) | S1 + continu | `docs/01-cadrage/backlog.md` (+ GitHub Projects) | ✅ |
| C17 | Développer les composants techniques et interfaces de l'application | S9 | `app/frontend/`, `app/backend/`, `docs/04-bloc3-app/dev-application.md` | ✅ |
| C18 | Automatiser les phases de tests du code source (CI) | S10 | `.github/workflows/ci-app.yml`, `docs/04-bloc3-app/ci.md` | ✅ |
| C19 | Créer un processus de livraison continue (CD) | S10 | `.github/workflows/cd-app.yml`, `docs/04-bloc3-app/cd.md` | ✅ |
| C20 | Surveiller une application IA (monitoring, journalisation) | S11 | `app/backend/common/logging_config.py`, `app/monitoring/`, `docs/04-bloc3-app/monitoring-app.md` | ✅ |
| C21 | Résoudre les incidents techniques | S11 | `docs/04-bloc3-app/incident-resolution.md` | ✅ |

## Notes

- Le libellé complet (officiel) de chaque compétence, ainsi que tous les critères d'évaluation associés, restent la référence : voir `Référentiel Dev IA Lyon P6.xlsx`. Cette matrice n'en est qu'un résumé de pilotage.
- C14, C15, C16 sont marquées ✅ dès S1 car leurs livrables de cadrage sont posés dans ce commit initial ; ils seront enrichis en continu (notamment C16, piloté au fil de l'eau via le board agile).
- Mettre à jour le statut à la fin de chaque semaine (voir `docs/00-pilotage/planning.md`).
