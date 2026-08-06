# NutriScan IA

Projet final de certification **Développeur en Intelligence Artificielle** (RNCP, Simplon Lyon, session 2026).

## Le projet

**NutriScan IA** aide un utilisateur ayant des allergies, intolérances ou un régime alimentaire particulier à vérifier rapidement la compatibilité d'un produit ou d'une recette : l'application collecte des données produits (Open Food Facts) et des recettes (scraping), les confronte au profil alimentaire de l'utilisateur via un service d'intelligence artificielle **exécuté en local**, et restitue une alerte de compatibilité, un score nutritionnel et des substitutions d'ingrédients.

**Choix de conception assumé** : toutes les sources de données et le service d'IA sont accessibles **sans création de compte ni de clé API** (Open Food Facts, fichier Ciqual, scraping, Ollama en local) — le projet reste entièrement reproductible sans démarche administrative.

> ⚠️ NutriScan IA est un outil d'aide à la lecture d'étiquettes et de recettes. Il ne constitue pas un avis médical.

Le projet est structuré pour couvrir, de façon traçable, les **21 compétences** du référentiel réparties sur ses **3 blocs** :

| Bloc | Contenu | Dossier code | Documentation |
|---|---|---|---|
| **Bloc 1** — Collecte, stockage, mise à disposition des données | API Open Food Facts, scraping recettes, fichier Ciqual, export OFF via DuckDB, PostgreSQL (Merise + RGPD), API REST Data | [`data-pipeline/`](data-pipeline) | [`docs/02-bloc1-data/`](docs/02-bloc1-data) |
| **Bloc 2** — Intégration d'un service d'IA | Veille, benchmark, POC Ollama (local), API REST IA, monitoring modèle, tests, CI/CD MLOps | [`ai-service/`](ai-service) | [`docs/03-bloc2-ia/`](docs/03-bloc2-ia) |
| **Bloc 3** — Application intégrant le service d'IA | Application Streamlit complète, CI/CD, monitoring, gestion d'incident | [`app/`](app) | [`docs/04-bloc3-app/`](docs/04-bloc3-app) |

## Pilotage du projet

- 📋 [Cahier des charges](docs/01-cadrage/cahier-des-charges.md), [user stories](docs/01-cadrage/user-stories.md), [modèle de données Merise](docs/01-cadrage/merise.md), [architecture technique](docs/01-cadrage/architecture.md)
- 🗓️ [Planning détaillé sur 13 semaines](docs/00-pilotage/planning.md)
- ✅ [Matrice de traçabilité des 21 compétences](docs/00-pilotage/matrice-competences.md) — vue d'ensemble de la conformité au référentiel, **complète**
- 📌 [Backlog agile](docs/01-cadrage/backlog.md)
- 🔒 [Registre RGPD](docs/rgpd) (dès S3) — attention particulière portée aux allergies, donnée de santé au sens de l'article 9 du RGPD
- 📝 [Rapports professionnels par épreuve (E1-E5)](docs/05-rapports-professionnels/README.md)

## Installation et lancement

```bash
git clone <url-du-depot> && cd 2026-08-05_projet_final_certification_devIA_session2
cp .env.example .env   # adapter les secrets si besoin (valeurs par defaut utilisables en local)

# Base de donnees + les trois API (Data, IA, backend applicatif)
docker compose up -d postgres api_data api_ia app_backend

# Modele IA local (hors conteneur, voir docs/03-bloc2-ia/poc.md)
ollama serve
ollama pull llama3.2:3b

# Import des donnees collectees (une fois, apres le premier demarrage de postgres)
cd data-pipeline && py -m load.import_data && cd ..

# Application (frontend Streamlit)
cd app && py -m streamlit run frontend/main.py
```

Monitoring applicatif (optionnel) : `docker compose up -d prometheus grafana`, tableau de bord sur `http://localhost:3000` (identifiants dans `.env`).

Chaque composant documente en détail sa propre procédure dans son README (`data-pipeline/`, `ai-service/`, `app/`) et sa documentation (`docs/02-bloc1-data/`, `docs/03-bloc2-ia/`, `docs/04-bloc3-app/`).

## Référentiel de certification

Ce dépôt suit le référentiel officiel « Développeur en Intelligence Artificielle » (Simplon, promotion Lyon P6, session Mars→Juin 2026) : 3 blocs de compétences, 5 épreuves de certification (E1 à E5), oral prévu mi-juin 2026.
