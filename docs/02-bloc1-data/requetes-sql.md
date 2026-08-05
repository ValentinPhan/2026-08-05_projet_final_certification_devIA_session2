# Requêtes SQL d'extraction (C2) — S2

## Requête analytique sur l'export Open Food Facts (`extract/duckdb_openfoodfacts.py`)

### Fonctionnement

La requête s'exécute directement sur le fichier distant `en.openfoodfacts.org.products.csv.gz` (~1,3 Go compressé, 4,65 millions de lignes) via le moteur **DuckDB** et son extension `httpfs`, sans téléchargement préalable :

```sql
WITH echantillon AS (
    SELECT code, countries_en, nutriscore_grade
    FROM read_csv('https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz',
                   delim='\t', header=true, sample_size=5000, ignore_errors=true)
    LIMIT 500000
)
SELECT nutriscore_grade, COUNT(*) AS nb_produits
FROM echantillon
WHERE countries_en ILIKE '%France%'
  AND nutriscore_grade IS NOT NULL
  AND nutriscore_grade NOT IN ('', 'unknown', 'not-applicable')
GROUP BY nutriscore_grade
ORDER BY nutriscore_grade
```

- **Sélection** : seules 3 colonnes sur les 211 disponibles sont projetées (`code`, `countries_en`, `nutriscore_grade`), le strict nécessaire pour la question posée.
- **Filtrage** : `WHERE` restreint aux produits vendus en France et aux Nutri-Score renseignés et exploitables (exclusion des valeurs `unknown`/`not-applicable`).
- **Agrégation** : `GROUP BY nutriscore_grade` avec `COUNT(*)`, triée par grade — répond à la question « quelle est la répartition des Nutri-Score des produits vendus en France ? ».
- **Résultat obtenu** (exécution de référence) :

  | Nutri-Score | Nb produits (échantillon) |
  |---|---|
  | a | 944 |
  | b | 912 |
  | c | 1677 |
  | d | 1872 |
  | e | 2982 |

### Optimisations appliquées (et pourquoi)

1. **Projection de colonnes** (`SELECT code, countries_en, nutriscore_grade` plutôt que `SELECT *`) : évite à DuckDB de matérialiser les 211 colonnes du fichier pour ne garder que 3 valeurs utiles, ce qui réduit fortement le volume réellement traité en mémoire.
2. **`LIMIT 500000` sur le flux brut** (dans le `WITH echantillon`, avant tout filtrage) : le fichier complet fait 4,65 millions de lignes ; le traiter en entier a été testé et écarté (voir point 3). Cette limite borne le temps d'exécution à une quinzaine de secondes tout en restant un échantillon représentatif (~11 % du fichier), et documente explicitement le compromis : retirer le `LIMIT` exécute la même requête sur l'intégralité du fichier, avec un temps d'exécution proportionnellement plus long.
3. **Choix du format source (CSV compressé en flux plutôt que Parquet distant)** : un premier essai a ciblé le miroir Parquet d'Open Food Facts hébergé sur Hugging Face (colonnes déjà typées, a priori plus adapté à une requête analytique). Mesuré en conditions réelles, ce miroir s'est révélé impraticable depuis cet environnement réseau : DuckDB multiplie les requêtes HTTP courtes pour lire les métadonnées Parquet (une par groupe de lignes), chaque aller-retour payant une latence réseau importante — une requête agrégée sur ce fichier était encore estimée à plusieurs dizaines de minutes après plusieurs pourcents d'avancement. Le CSV compressé, lu en flux séquentiel simple, ne présente pas ce défaut (5 Mo transférés en ~1 seconde en test direct) : ce choix, a priori contre-intuitif (CSV plutôt que Parquet), est documenté ici précisément parce qu'il découle d'une mesure et non d'une préférence par défaut.
4. **`sample_size=5000` et `ignore_errors=true`** sur `read_csv` : limite l'effort de détection automatique des types de colonnes (le fichier a 211 colonnes hétérogènes) et tolère les lignes mal formées ponctuelles sans interrompre tout le traitement.

## Requêtes SQL d'import (Bloc 1, S3)

Les requêtes SQL de création du schéma et d'import en base PostgreSQL (issues du MLD, voir [`docs/01-cadrage/merise.md`](../01-cadrage/merise.md)) seront ajoutées ici lors de la semaine S3, avec le script `data-pipeline/db/schema.sql`.
