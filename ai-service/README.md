# AI Service — Bloc 2

Veille, benchmark, POC et exposition du service d'IA de **NutriScan IA** : détection d'allergènes/ingrédients incompatibles dans un produit ou une recette, à partir d'un modèle exécuté **en local via Ollama** (aucune clé API requise).

Couvre les compétences **C6 à C13** — épreuves **E2 + E3** (semaines S4-S8). **Complet.**

## Structure

```
ai-service/
├── common/             # code partagé au sein du composant (allergènes, client API Data, utils)
├── veille/             # script d'agrégation de veille technique et réglementaire (C6)
├── poc/                # preuve de concept d'extraction (Ollama) (C8)
├── api_ia/             # API REST FastAPI exposant l'analyse de compatibilité, avec ses tests (C9, C10, C12)
└── monitoring/         # évaluation du modèle + journalisation MLflow (C11)
```

Le benchmark des services IA (C7) est un livrable documentaire, sans code associé — voir [`docs/03-bloc2-ia/benchmark-services-ia.md`](../docs/03-bloc2-ia/benchmark-services-ia.md).

Documentation détaillée : [docs/03-bloc2-ia](../docs/03-bloc2-ia). Planning : [docs/00-pilotage/planning.md](../docs/00-pilotage/planning.md).
