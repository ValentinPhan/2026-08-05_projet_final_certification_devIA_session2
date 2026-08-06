# Application — Bloc 3

Application complète **NutriScan IA** intégrant le service d'IA : compte utilisateur, profil alimentaire (allergies/régime), recherche de produits/recettes, alerte de compatibilité et score nutritionnel.

Couvre les compétences **C14 à C21** — épreuves **E4 + E5** (semaines S1, S9-S11). **C14 à C17 complets.**

## Structure

```
app/
├── frontend/
│   ├── main.py          # application complète (C17, S9) : compte, profil persistant, historique, RGPD
│   └── prototype.py      # prototype de démonstration (C10, S6) — conservé pour sa documentation
├── backend/              # API FastAPI applicative : auth, profil chiffré, historique, droits RGPD (C17, S9)
├── tests/                # tests d'intégration bout-en-bout de l'application (prototype)
├── monitoring/           # Prometheus / Grafana + journalisation applicative (S11)
└── incidents/            # incidents simulés et documentation de résolution (S11)
```

`frontend/main.py` appelle les trois API du système (Data, IA, backend applicatif) en HTTP — il ne se connecte jamais directement à PostgreSQL, seul `backend/` en a le droit (et uniquement sur ses propres tables, voir [dev-application.md](../docs/04-bloc3-app/dev-application.md)).

Installation et lancement :

```bash
docker compose up -d postgres api_data api_ia app_backend
ollama serve
cd app
py -m streamlit run frontend/main.py
```

Documentation détaillée du Bloc 3 : [docs/04-bloc3-app](../docs/04-bloc3-app).

Planning : [docs/00-pilotage/planning.md](../docs/00-pilotage/planning.md).
