# Planning 13 semaines — NutriScan IA

Adaptation du planning de formation Simplon (`Planning Dev IA Lyon Simplon 2026.xlsx`) au projet NutriScan IA. Dates indicatives, à recaler sur la date réelle de démarrage.

| S | Dates | Phase | Épreuve | Bloc | Comp. | Objectifs NutriScan IA | Livrables |
|---|---|---|---|---|---|---|---|
| S1 | 17→21/03 | Cadrage projet | E4 | B3 | C14,C15,C16 | Cahier des charges, user stories, MCD/MLD Merise, choix architecture (data-pipeline / ai-service / app), setup backlog agile | `docs/01-cadrage/*` |
| S2 | 24→28/03 | Collecte de données | E1 | B1 | C1,C2,C3 | Appel à l'API Open Food Facts, scraping d'un site de recettes, chargement du fichier Ciqual, requête DuckDB sur l'export complet Open Food Facts, script d'agrégation/nettoyage | `data-pipeline/extract/`, `data-pipeline/transform/` |
| S3 | 31/03→04/04 | BDD + API Data | E1 | B1 | C4,C5 | Base PostgreSQL (modèle Merise, chiffrement des données de santé), script d'import, registre RGPD, API FastAPI (produits/recettes/nutrition), doc Swagger | `data-pipeline/db/`, `data-pipeline/api_data/`, `docs/rgpd/` |
| S4 | 07→11/04 | Veille + benchmark IA | E2 | B2 | C6,C7 | Veille réglementaire (RGPD art. 9 données de santé, règlement INCO allergènes, IA Act sur les usages santé), benchmark de services d'extraction d'ingrédients/allergènes (cloud vs local Ollama) | `docs/03-bloc2-ia/veille.md`, `docs/03-bloc2-ia/benchmark-services-ia.md` |
| S5 | 14→18/04 | POC service IA | E2 | B2 | C8 | Installation/configuration d'Ollama en local, test de faisabilité sur l'extraction d'allergènes depuis un texte d'ingrédients | `ai-service/poc/` |
| S6 | 21→25/04 | API IA + prototype | E3 | B2 | C9,C10 | API FastAPI exposant l'analyse de compatibilité, prototype Streamlit de démonstration | `ai-service/api_ia/`, `app/frontend/prototype.py` |
| S7 | 28/04→02/05 | Monitoring modèle + tests | E3 | B2 | C11,C12 | MLflow/Grafana pour la précision de détection d'allergènes et la latence d'inférence locale, tests pytest du pipeline IA | `ai-service/monitoring/`, `ai-service/tests/` |
| S8 | 05→09/05 | CI/CD MLOps | E3 | B2 | C13 | Pipeline GitHub Actions : tests données → évaluation du modèle → packaging Docker | `.github/workflows/mlops-ci-cd.yml` |
| S9 | 12→16/05 | Application complète | E4 | B3 | C17 | App Streamlit complète : auth, profil alimentaire, recherche produits/recettes, alertes allergènes, score nutritionnel ; sécurité OWASP, accessibilité WCAG | `app/frontend/`, `app/backend/` |
| S10 | 19→23/05 | CI/CD Application | E4 | B3 | C18,C19 | Pipeline CI (tests, lint) + CD (build Docker, déploiement pré-prod) | `.github/workflows/ci-app.yml`, `.github/workflows/cd-app.yml` |
| S11 | 26→30/05 | Monitoring app + incident | E5 | B3 | C20,C21 | Prometheus/Grafana + logs structurés, simulation et résolution documentée d'un incident (ex. panne de l'API Open Food Facts) | `app/monitoring/`, `app/incidents/` |
| S12 | 02→06/06 | Finalisation + rapport | - | - | Toutes | Rédaction des rapports professionnels (E1 : 2-5 p. / E2,E3,E4 : 15-20 p. / E5 : 2-5 p.), mise à jour de la matrice de compétences, nettoyage des dépôts | Rapports pro, `docs/00-pilotage/matrice-competences.md` à jour |
| S13 | 09→13/06 | Préparation oral | - | - | Toutes | Support de présentation, démo fonctionnelle, soutenances blanches, anticipation des questions du jury | Slides, script de démo |

## Épreuves — rappel

- **E1** Mise en situation (C1-C5) : rapport pro 2-5 p., oral 15 min + 10 min de questions.
- **E2** Cas pratique (C6-C8) : rapport pro 15-20 p., oral 15 min + 10 min de questions.
- **E3** Mise en situation (C9-C13) : rapport pro 15-20 p., oral 20 min + démo.
- **E4** Mise en situation (C14-C19) : rapport pro 15-20 p., oral 20 min + démo.
- **E5** Cas pratique (C20-C21) : doc technique 2-5 p., oral 10 min + 10 min de questions.

## Suivi

Le détail compétence par compétence est dans [`matrice-competences.md`](matrice-competences.md). Mettre à jour son statut à la fin de chaque semaine.
