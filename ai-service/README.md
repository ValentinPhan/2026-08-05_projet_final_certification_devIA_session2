# AI Service — Bloc 2

Veille, benchmark, POC et exposition du service d'IA de **NutriScan IA** : détection d'allergènes/ingrédients incompatibles dans un produit ou une recette, à partir d'un modèle exécuté **en local via Ollama** (aucune clé API requise).

Couvre les compétences **C6 à C13** — épreuves **E2 + E3** (semaines S4-S8).

## Structure prévue

```
ai-service/
├── veille/           # synthèses de veille technique et réglementaire
├── benchmark/        # comparatif des services IA candidats (cloud vs local)
├── poc/                # preuve de concept du service retenu (Ollama)
├── api_ia/            # API REST FastAPI exposant l'analyse de compatibilité
├── monitoring/         # MLflow / Grafana : métriques du modèle
└── tests/               # tests automatisés du pipeline IA (données, éval)
```

Ces dossiers seront peuplés en S4-S8. Documentation détaillée : [docs/03-bloc2-ia](../docs/03-bloc2-ia).

Planning : [docs/00-pilotage/planning.md](../docs/00-pilotage/planning.md).
