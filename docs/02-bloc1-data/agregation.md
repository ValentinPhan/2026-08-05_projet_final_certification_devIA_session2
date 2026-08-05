# Agrégation et nettoyage des données (C3) — S2

## Script

[`transform/clean_aggregate.py`](../../data-pipeline/transform/clean_aggregate.py) — dépendances : `pandas` (voir [`requirements.txt`](../../data-pipeline/requirements.txt)).

**Commandes** (après avoir exécuté les scripts d'extraction, voir [`extraction.md`](extraction.md)) :

```bash
cd data-pipeline
py -m transform.clean_aggregate
```

**Entrées** : `data/raw/openfoodfacts/openfoodfacts_products.json`, `data/raw/recettes/recettes.json`, `data/raw/ciqual/ciqual_composition.csv`.
**Sorties** : `data/processed/produits.json`, `data/processed/recettes.json`, `data/processed/composition_nutritionnelle.csv`.

## Enchaînement logique

1. Chargement du fichier brut correspondant (JSON ou CSV). Si un fichier d'extraction est absent, l'étape est journalisée et ignorée sans faire échouer les autres (les trois sources sont indépendantes).
2. Application des règles de nettoyage propres à chaque source (détaillées ci-dessous).
3. Sauvegarde du jeu de données consolidé, prêt pour l'import en base (S3).

## Choix de nettoyage et d'homogénéisation

### Produits (Open Food Facts) — `clean_produits`

- **Déduplication** : par `code_barres`, au cas où une même fiche serait retournée par plusieurs termes de recherche.
- **Suppression des entrées corrompues** : un produit sans nom (`product_name`) ou sans texte d'ingrédients est inexploitable pour la fonctionnalité de détection d'allergènes — ces entrées sont écartées plutôt que conservées avec des champs vides. Constat d'exécution (échantillon de référence) : sur 47 produits récupérés, 21 ont été écartés pour ce motif (beaucoup de fiches Open Food Facts anciennes n'ont pas de texte d'ingrédients renseigné), 26 conservés.
- **Homogénéisation** : espaces multiples et espaces de début/fin supprimés sur les champs texte (`_clean_text`) ; catégorie ramenée à un libellé lisible à partir du premier tag Open Food Facts (`en:biscuits` → `biscuits`) ; Nutri-Score normalisé en minuscule, ou `None` si absent/`unknown` plutôt que la chaîne brute Open Food Facts.

### Recettes (scraping) — `clean_recettes`

- **Suppression des entrées corrompues** : une recette sans ingrédient exploitable est écartée (aucun cas rencontré sur le corpus de 10 recettes actuel, règle défensive pour une collecte élargie).
- **Homogénéisation** : titre débarrassé du préfixe technique Wikibooks (`Livre de cuisine/Ratatouille` → `Ratatouille`) ; chaque ingrédient débarrassé de sa virgule de fin de ligne héritée du wikitexte et des espaces superflus.
- **Choix documenté plutôt que masqué** : une recette dont la section « Préparation » n'a pas pu être extraite (structure de page différente) est **conservée** — les ingrédients seuls restent utiles à la fonctionnalité de détection d'allergènes — mais le cas est comptabilisé et journalisé (`incomplete_instructions`) pour rester traçable dans le rapport qualité plutôt que silencieusement ignoré.

### Composition nutritionnelle (Ciqual) — `clean_ciqual`

- **Suppression des entrées corrompues** : lignes sans libellé d'aliment supprimées ; lignes où les 4 valeurs nutritionnelles retenues (énergie, protéines, glucides, lipides) sont toutes manquantes supprimées (une ligne Ciqual sans aucune de ces valeurs n'apporte rien au calcul du score nutritionnel).
- **Déduplication** : par `code_ciqual`.
- Constat d'exécution : 3178 aliments conservés sur 3186 chargés.

## Traçabilité

Le script journalise, pour chaque source, le nombre d'entrées conservées et le motif de chaque exclusion (sans code, incomplet, doublon) — ces compteurs constituent la preuve d'exécution reproductible à joindre au rapport professionnel de l'épreuve E1.
