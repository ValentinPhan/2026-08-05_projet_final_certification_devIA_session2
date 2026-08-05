# Data Pipeline — Bloc 1

Collecte, agrégation, stockage et mise à disposition des données de **NutriScan IA** : produits alimentaires (Open Food Facts), recettes (scraping), table de composition nutritionnelle (Ciqual/ANSES).

Couvre les compétences **C1, C2, C3, C4, C5** — épreuve **E1** (semaines S2-S3).

## Structure prévue

```
data-pipeline/
├── extract/        # collecte : API Open Food Facts, scraping recettes, fichier Ciqual, requête DuckDB sur l'export OFF
├── transform/       # nettoyage, dédoublonnage, homogénéisation des formats
├── load/             # import en base PostgreSQL
├── db/                # schéma SQL (issu du MLD), migrations
└── api_data/          # API REST FastAPI exposant produits/recettes/nutrition
```

Ces dossiers seront peuplés en S2-S3. Documentation fonctionnelle et technique détaillée : [docs/02-bloc1-data](../docs/02-bloc1-data).

Planning : [docs/00-pilotage/planning.md](../docs/00-pilotage/planning.md).
