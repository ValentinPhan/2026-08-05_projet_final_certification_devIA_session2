# Rapport professionnel — Épreuve E1 (Mise en situation, C1-C5)

**Projet** : NutriScan IA — assistant de compatibilité alimentaire (allergies/intolérances)
**Bloc** : B1 — Automatisation de la collecte et de la mise à disposition des données
**Semaines** : S2-S3 · **Compétences** : C1 (extraction multi-source), C2 (requêtes SQL), C3 (agrégation), C4 (base de données conforme RGPD), C5 (API REST Data)

## 1. Contexte et objectif

NutriScan IA aide un utilisateur ayant des allergies, intolérances ou un régime alimentaire particulier à vérifier la compatibilité d'un produit ou d'une recette. Le Bloc 1 fournit la matière première de cette fonctionnalité : des données produits, des recettes, une table de référence nutritionnelle officielle, et un référentiel des allergènes — collectées, nettoyées, stockées et exposées de façon fiable et traçable aux composants qui en dépendent (le service IA du Bloc 2, l'application du Bloc 3).

Contrainte de conception posée dès le cadrage et respectée sur l'ensemble du bloc : **aucune source de donnée ne nécessite de compte ni de clé API**, pour garantir la reproductibilité du projet sans démarche administrative.

## 2. Réalisations et preuves d'exécution

### C1 — Extraction multi-source

Le référentiel exige un mix de sources ; les quatre types couverts et leurs résultats mesurés :

| Source | Type | Script | Résultat réel |
|---|---|---|---|
| Open Food Facts | Service web REST | `extract/openfoodfacts_api.py` | 48 codes découverts, 47 fiches récupérées (1 × 404 normal) |
| Wikibooks *Livre de cuisine* | Scraping (licence CC BY-SA) | `extract/scrape_recettes.py` | 10/10 recettes récupérées |
| Ciqual (ANSES) | Fichier de données | `extract/ciqual_loader.py` | 3186 aliments chargés |
| Export complet Open Food Facts | Système big data | `extract/duckdb_openfoodfacts.py` | requête sur 500 000 lignes d'un export de 4,65 M lignes |

Détail dans [`docs/02-bloc1-data/extraction.md`](../02-bloc1-data/extraction.md).

### C2 — Requêtes SQL d'extraction

La requête analytique DuckDB (voir [`requetes-sql.md`](../02-bloc1-data/requetes-sql.md)) répond à une question métier réelle (répartition des Nutri-Score des produits vendus en France) avec trois optimisations documentées et justifiées par la mesure, pas par principe : projection de colonnes, échantillonnage borné, et un choix de format contre-intuitif (CSV compressé en flux plutôt que Parquet distant) retenu après avoir mesuré que le second était impraticable dans cet environnement réseau.

### C3 — Agrégation multi-source

`transform/clean_aggregate.py` applique à chaque source des règles de nettoyage propres (déduplication, suppression des entrées corrompues, homogénéisation des formats) et journalise systématiquement les motifs d'exclusion plutôt que de les masquer — ce compteur constitue la preuve d'exécution reproductible (ex. 26/47 produits conservés, 21 écartés pour absence de texte d'ingrédients exploitable).

### C4 — Base de données conforme RGPD

Modélisation Merise complète (MCD → MLD, voir [`merise.md`](../01-cadrage/merise.md)), traduite en schéma PostgreSQL rejouable (`data-pipeline/db/schema.sql`). La donnée de santé (profil allergène, `UTILISATEUR_ALLERGENE.niveau_chiffre`) est **chiffrée au repos** avec `pgcrypto`, clé applicative hors base. Le registre des traitements ([`docs/rgpd/registre-traitements.md`](../rgpd/registre-traitements.md)) couvre les 4 traitements identifiés, leur base légale, et les droits des personnes concernées (accès, effacement, portabilité) — implémentés concrètement en S9 et vérifiés dans le navigateur.

### C5 — API REST Data

`data-pipeline/api_data/` (FastAPI, documentation OpenAPI automatique) expose produits, recettes, nutrition et référentiel allergènes, avec authentification JWT *client credentials* et un périmètre de sécurité volontairement restreint : **aucune donnée personnelle** n'y transite, par construction — même en cas de compromission de cette API, aucune donnée de santé ne serait exposée. Chaîne testée de bout en bout via `docker compose up` (voir preuves dans [`api-data.md`](../02-bloc1-data/api-data.md)).

## 3. Difficultés rencontrées et résolues

Conformément à la méthodologie suivie sur tout le projet (vérifier plutôt que supposer), plusieurs problèmes réels ont été trouvés et corrigés en exécutant effectivement le code, pas en le relisant :

- **`robots.txt` faussement bloquant** : le parseur standard de Python échoue silencieusement sur Wikibooks (l'agent HTTP par défaut reçoit un 403, qui bascule le parseur en « tout interdire »). Contourné en récupérant `robots.txt` avec un en-tête `User-Agent` explicite avant de le transmettre au parseur.
- **Incompatibilité Python 3.9 / Pydantic v2** : la syntaxe `str | None` (PEP 604) fait planter l'API au démarrage sur l'environnement de développement cible. Remplacée systématiquement par `typing.Optional`.
- **Conflit de port et interception TLS locale** : deux problèmes d'environnement (port 8001 déjà occupé, proxy TLS interceptant les téléchargements pip dans Docker) diagnostiqués et contournés sans complexifier la configuration par défaut livrée.
- **Miroir Parquet impraticable** : mesuré (et non supposé) inadapté à cet environnement réseau avant d'être écarté au profit du CSV compressé — décision documentée avec les chiffres qui la justifient plutôt que présentée comme une évidence.

## 4. Auto-évaluation et limites assumées

Les cinq compétences sont couvertes avec des preuves d'exécution reproductibles (compteurs réels, requêtes HTTP réellement exécutées, capture de statuts HTTP). Deux limites assumées, documentées plutôt que masquées :

- Le corpus de recettes (10 entrées) et l'échantillon de produits (47 fiches) sont volontairement restreints pour un projet pédagogique solo sur 13 semaines ; le code (pagination, gestion des erreurs 429/5xx, retries) est conçu pour supporter un volume plus grand sans modification.
- L'échantillon DuckDB (500 000 lignes sur 4,65 M) est un compromis temps d'exécution/représentativité explicitement documenté, pas une limite technique de l'outil — retirer le `LIMIT` exécute la même requête sur l'export complet.

## 5. Ce qui serait fait différemment

Avec plus de temps, la table Ciqual serait rapprochée des ingrédients de recette *pendant* l'import (S3) plutôt qu'ajoutée a posteriori en S9 lorsque le score nutritionnel du Bloc 3 en a révélé le besoin réel — ce séquencement a fonctionné (le retour en arrière a été rapide et documenté), mais l'anticiper aurait évité une dépendance tardive d'un bloc sur un autre.

## 6. Conclusion

Le Bloc 1 livre une chaîne de collecte, nettoyage et mise à disposition des données complète, testée en conditions réelles à chaque étape, et conforme aux exigences RGPD dès la modélisation — fondation solide pour les Blocs 2 et 3 qui en dépendent directement.
