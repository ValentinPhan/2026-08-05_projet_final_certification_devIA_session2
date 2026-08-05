# API REST Data (C5) — S3

## Présentation

[`data-pipeline/api_data/`](../../data-pipeline/api_data) expose en lecture les données collectées et nettoyées au Bloc 1 (produits, recettes, composition nutritionnelle Ciqual, référentiel des 14 allergènes) aux autres composants du système (application du Bloc 3, service IA du Bloc 2). Construite avec **FastAPI**, qui génère automatiquement une documentation conforme au standard **OpenAPI** : `http://localhost:8010/docs` (Swagger UI) une fois le serveur lancé.

## Périmètre de sécurité volontaire

Cette API **n'expose et ne modifie aucune donnée personnelle** : pas de comptes utilisateurs, pas de profils allergènes individuels, pas d'historique d'analyse. Ces données relèvent exclusivement de l'application (Bloc 3) et de sa propre logique d'accès. Ce choix de périmètre est en soi une mesure de sécurité par conception : même en cas de compromission de cette API, aucune donnée personnelle ou de santé ne pourrait être exposée.

## Authentification

Schéma **client credentials** (JWT), adapté à une API consommée par d'autres services plutôt que directement par un utilisateur final (l'authentification utilisateur vit dans l'application, Bloc 3) :

1. `POST /auth/token?client_id=...&client_secret=...` → renvoie un jeton Bearer valide 30 minutes.
2. Toutes les autres routes de données exigent l'en-tête `Authorization: Bearer <jeton>` ; son absence ou son invalidité renvoie `401`.

Identifiants et clé de signature lus depuis l'environnement (`JWT_SECRET_KEY`, `API_CLIENT_ID`, `API_CLIENT_SECRET`, voir [`.env.example`](../../.env.example)) — jamais codés en dur.

## Endpoints

| Méthode | Route | Auth | Description |
|---|---|---|---|
| GET | `/health` | non | Vérifie que l'API est en ligne |
| POST | `/auth/token` | non | Émet un jeton d'accès |
| GET | `/allergenes` | oui | Référentiel des 14 allergènes à déclaration obligatoire |
| GET | `/produits` | oui | Liste les produits (filtres `categorie`, `nutri_score`, pagination `limit`/`offset`) |
| GET | `/produits/{code_barres}` | oui | Détail d'un produit + ses allergènes (404 si absent) |
| GET | `/recettes` | oui | Liste les recettes (pagination) |
| GET | `/recettes/{id_recette}` | oui | Détail d'une recette + ses ingrédients (404 si absent) |
| GET | `/nutrition/{code_ciqual}` | oui | Composition nutritionnelle officielle Ciqual (404 si absent) |

## Preuves d'exécution (vérifiées de bout en bout via `docker compose up`)

```bash
curl http://localhost:8010/health
# {"status":"ok"}

curl http://localhost:8010/produits
# {"detail":"Not authenticated"}   → 401, accès bien restreint sans jeton

curl -X POST "http://localhost:8010/auth/token?client_id=nutriscan-app&client_secret=<API_CLIENT_SECRET>"
# {"access_token":"...", "token_type":"bearer", "expires_in_minutes":30}

curl -H "Authorization: Bearer <token>" http://localhost:8010/produits/0072417144592
# 200, fiche produit complète avec ses 3 allergènes détectés

curl -H "Authorization: Bearer <token>" http://localhost:8010/produits/0000000000000
# 404 {"detail":"Produit introuvable"}
```

## Installation et lancement

```bash
cp .env.example .env   # adapter les secrets
docker compose up -d --build
py -m load.import_data   # depuis data-pipeline/, une fois la base prete
```

L'API est alors accessible sur `http://localhost:8010` (documentation interactive sur `/docs`).

## Difficultés rencontrées et résolues

- **Compatibilité Python 3.9** : la syntaxe `str | None` (PEP 604, Python 3.10+) fait planter Pydantic v2 au démarrage sur l'environnement de développement (Python 3.9). Remplacée par `typing.Optional[str]` dans [`schemas.py`](../../data-pipeline/api_data/schemas.py) et [`main.py`](../../data-pipeline/api_data/main.py).
- **Conflit de port** : le port `8001` initialement prévu pour l'API entrait en conflit avec une application locale déjà installée sur le poste de développement (liaison `127.0.0.1:8001` prioritaire sur la liaison `0.0.0.0:8001` de Docker). Port documenté déplacé sur `8010`.
- **Build Docker derrière un réseau restreint** : l'installation des dépendances Python echouait dans l'image Docker à cause d'une interception TLS locale à l'environnement de développement. Un `ARG PIP_EXTRA_ARGS` (vide par défaut, donc vérification TLS active dans l'image livrée) permet de passer un contournement ponctuel sans l'imposer à tous les environnements : `docker compose build --build-arg PIP_EXTRA_ARGS="--trusted-host pypi.org --trusted-host files.pythonhosted.org"`.
