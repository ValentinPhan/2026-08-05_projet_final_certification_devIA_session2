# Extraction des données (C1) — S2

## Spécifications techniques

- **Technologies et outils** : Python 3.11+, `requests` (appels HTTP), `beautifulsoup4` + `lxml` (parsing HTML), `duckdb` (moteur analytique big data), `pandas`/`xlrd` (lecture Excel). Voir [`data-pipeline/requirements.txt`](../../data-pipeline/requirements.txt).
- **Services externes sollicités** : API Open Food Facts (recherche + fiche produit), site `fr.wikibooks.org` (scraping), fichier Ciqual publié sur `data.gouv.fr`, export public Open Food Facts (`static.openfoodfacts.org`).
- **Exigences de programmation** : chaque script est un module Python autonome (point d'entrée `run()` + bloc `if __name__ == "__main__"`), sans dépendance à un compte ni une clé API.
- **Accessibilité (disponibilité/accès)** : toutes les sources sont publiques, disponibles sans authentification ; seule contrainte de "politesse" : en-tête `User-Agent` identifiant le projet, délais entre requêtes, et respect de `robots.txt` pour le scraping.
- **Périmètre couvert** : le mix de sources exigé par le référentiel est respecté — service web REST (Open Food Facts), fichier de données (Ciqual), scraping (Wikibooks), système big data (export Open Food Facts interrogé via DuckDB). La base de données (5ᵉ source) est traitée en S3 (`data-pipeline/db/`).

## Scripts

### `extract/openfoodfacts_api.py` — API REST (service web)

- **Source** : [Open Food Facts](https://world.openfoodfacts.org) — API publique, aucune clé. Deux endpoints combinés : `search.openfoodfacts.org/search` (découverte de codes-barres par recherche plein texte) et `world.openfoodfacts.org/api/v2/product/<code>.json` (fiche produit complète — plus stable, utilisé pour la donnée détaillée).
- **Point de lancement** : fonction `run()`, exécutable via `py extract/openfoodfacts_api.py`.
- **Initialisation** : session HTTP `requests` avec en-tête `User-Agent` dédié ; aucune connexion à initialiser (API sans état).
- **Logique** : pour chaque terme de recherche (`SEARCH_TERMS`), découverte de codes-barres candidats, puis récupération de la fiche complète de chaque code.
- **Gestion des erreurs** : `_get_with_retry` intercepte les réponses `429` (limitation de débit) et `5xx`, et retente jusqu'à 3 fois avec un délai croissant (ou la valeur de l'en-tête `Retry-After` si présent) ; un `404` (produit supprimé) est journalisé et ignoré sans interrompre le script.
- **Fin de traitement** : sauvegarde de la liste de produits dans `data-pipeline/data/raw/openfoodfacts/openfoodfacts_products.json`.
- **Constat d'exécution** (à date de rédaction, rejouable) : 48 codes découverts, 47 fiches récupérées avec succès (1 produit introuvable en 404, cas normal).

### `extract/scrape_recettes.py` — scraping

- **Source choisie et justifiée** : le Wikibooks francophone *Livre de cuisine* (`fr.wikibooks.org`), dont le contenu est sous licence libre CC BY-SA — contrairement à la plupart des sites de recettes commerciaux, dont les CGU interdisent explicitement le scraping. Ce choix lève toute ambiguïté juridique pour un projet pédagogique.
- **Contrainte technique identifiée et vérifiée avant collecte** : le fichier `robots.txt` du site est récupéré puis analysé programmatiquement (`_check_robots_txt`) avant toute requête de page ; chaque URL cible est validée par `robots.can_fetch(...)` avant d'être appelée. Point d'attention documenté : `urllib.robotparser.read()` échoue silencieusement sur ce site (l'agent HTTP par défaut d'`urllib` reçoit une réponse 403, ce qui bascule le parseur en "tout interdire") — le script contourne ce problème en récupérant lui-même `robots.txt` avec son propre en-tête `User-Agent` avant de le transmettre au parseur.
- **Logique** : liste de 10 recettes ciblées (`RECIPE_TITLES`, vérifiées manuellement disponibles), récupération de chaque page, extraction du titre, de la section « Ingrédients » (liste `<ul>`) et de la section « Préparation » (liste `<ol>`) par repérage des titres de section (comparaison insensible aux accents).
- **Gestion des erreurs** : nouvelle tentative (jusqu'à 3) sur erreur réseau ou réponse `5xx` ; un `404` ou une page dont la structure ne contient pas d'ingrédients est journalisé et ignoré.
- **Fin de traitement** : chaque page brute est sauvegardée (`data/raw/recettes/<slug>.html`, traçabilité) et les données structurées dans `data/raw/recettes/recettes.json`.
- **Constat d'exécution** : 10/10 recettes récupérées et parsées avec succès.

### `extract/ciqual_loader.py` — fichier de données

- **Source** : table Ciqual (ANSES), fichier Excel officiel publié sans compte sur `data.gouv.fr`.
- **Logique** : téléchargement du fichier une première fois (mis en cache localement dans `data/raw/ciqual/ciqual.xls` pour ne pas re-solliciter la source à chaque exécution), lecture de la feuille `compo`, sélection et renommage des colonnes utiles au projet, conversion des valeurs (virgule décimale française, marqueurs Ciqual `-` = non déterminé, `< x` = sous le seuil de quantification assimilé à 0).
- **Gestion des erreurs** : `response.raise_for_status()` sur le téléchargement ; valeurs non convertibles regroupées et journalisées en une seule ligne de synthèse (plutôt qu'un flot de messages), sans interrompre le traitement.
- **Fin de traitement** : sauvegarde dans `data/raw/ciqual/ciqual_composition.csv`.
- **Constat d'exécution** : 3186 aliments chargés.

### `extract/duckdb_openfoodfacts.py` — système big data

Voir [`requetes-sql.md`](requetes-sql.md) pour le détail de la requête et des optimisations.

## Dépendances et exécution

```bash
cd data-pipeline
py -m pip install -r requirements.txt
py -m extract.openfoodfacts_api
py -m extract.scrape_recettes
py -m extract.ciqual_loader
py -m extract.duckdb_openfoodfacts
```

Tous les scripts sont versionnés dans ce dépôt Git (`data-pipeline/extract/`).
