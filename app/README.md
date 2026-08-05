# Application — Bloc 3

Application complète **NutriScan IA** intégrant le service d'IA : compte utilisateur, profil alimentaire (allergies/régime), recherche de produits/recettes, alerte de compatibilité et score nutritionnel.

Couvre les compétences **C14 à C21** — épreuves **E4 + E5** (semaines S1, S9-S11).

## Structure prévue

```
app/
├── frontend/        # interface Streamlit (accessible, WCAG)
├── backend/          # logique métier applicative, auth, orchestration des appels API
├── tests/              # tests unitaires / intégration de l'application
├── monitoring/         # Prometheus / Grafana + journalisation applicative
└── incidents/          # incidents simulés et documentation de résolution
```

`frontend/prototype.py` existe dès S6 (prototype de démonstration, compétence C10 du Bloc 2, voir [docs/03-bloc2-ia/prototype.md](../docs/03-bloc2-ia/prototype.md)) — l'application complète (avec compte utilisateur et persistance) sera développée à partir de S9. Documentation détaillée du Bloc 3 : [docs/04-bloc3-app](../docs/04-bloc3-app).

Planning : [docs/00-pilotage/planning.md](../docs/00-pilotage/planning.md).
