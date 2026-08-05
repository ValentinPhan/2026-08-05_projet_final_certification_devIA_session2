# Cahier des charges — NutriScan IA

## 1. Contexte et enjeux

Un consommateur allergique, intolérant ou suivant un régime alimentaire particulier (sans gluten, végétarien, sans lactose…) doit aujourd'hui lire manuellement la liste d'ingrédients de chaque produit ou recette pour vérifier sa compatibilité — un exercice fastidieux et source d'erreurs, notamment sur des recettes qui ne mentionnent pas explicitement les allergènes.

**NutriScan IA** est une application qui automatise cette vérification : l'utilisateur définit un profil alimentaire (allergies, intolérances, régime), recherche un produit (via les données ouvertes Open Food Facts) ou une recette, et reçoit une analyse de compatibilité générée par un service d'intelligence artificielle, accompagnée d'un score nutritionnel et de substitutions proposées en cas d'incompatibilité.

Le projet sert de support à la certification **Développeur en Intelligence Artificielle** (RNCP, Simplon) et doit démontrer la maîtrise des 21 compétences du référentiel, réparties sur les 3 blocs (collecte/données, intégration IA, application complète).

**Contrainte de conception assumée** : toutes les sources de données et le service d'IA sont accessibles **sans création de compte ni de clé API**, afin de garder le projet reproductible par un tiers sans démarche administrative (API publique Open Food Facts, fichier ouvert Ciqual, scraping, modèle d'IA exécuté en local via Ollama).

**Avertissement produit** : NutriScan IA est un outil d'aide à la lecture d'étiquettes et de recettes ; il ne constitue en aucun cas un avis médical et ne se substitue pas à un professionnel de santé. Ce disclaimer est affiché de façon visible dans l'application (voir `user-stories.md`).

## 2. Acteurs

| Acteur | Rôle |
|---|---|
| Utilisateur (consommateur) | Crée un profil alimentaire, recherche des produits/recettes, consulte les analyses de compatibilité |
| Développeur IA (le porteur du projet) | Conçoit, développe, teste, déploie et maintient l'ensemble de la chaîne |
| Jury de certification | Évalue la conformité du livrable au référentiel de compétences |
| Sources de données tierces | Open Food Facts (API + export complet), ANSES (table Ciqual), site de recettes public (scraping) |
| Service d'intelligence artificielle | Modèle exécuté localement (Ollama), retenu après veille et benchmark documentés (bloc 2) |

## 3. Objectifs fonctionnels

- Permettre à un utilisateur de créer un compte et de définir un profil alimentaire (allergies, intolérances, régime).
- Permettre la recherche d'un produit alimentaire (nom ou code-barres) via les données Open Food Facts.
- Permettre la recherche d'une recette parmi un corpus collecté par scraping.
- Détecter automatiquement, via IA, les allergènes/ingrédients incompatibles avec le profil de l'utilisateur, pour un produit comme pour une recette.
- Calculer un score nutritionnel à partir des données Ciqual et/ou Open Food Facts.
- Proposer des substitutions d'ingrédients en cas d'incompatibilité.
- Conserver un historique des recherches et analyses de l'utilisateur.
- Garantir à l'utilisateur la maîtrise de ses données personnelles, en particulier de la donnée sensible que constituent ses allergies (accès, export, suppression).

## 4. Objectifs techniques

- Architecture en 3 composants faiblement couplés, chacun exposé via API REST documentée : `data-pipeline` (données), `ai-service` (IA), `app` (application utilisateur).
- Base de données relationnelle modélisée selon la méthode Merise, conforme RGPD, avec une attention particulière portée à la donnée de santé (allergies = catégorie particulière au sens de l'article 9 du RGPD).
- Service d'IA exécuté **localement** (Ollama), choisi après une veille et un benchmark documentés, pour garantir qu'aucune donnée personnelle de santé ne transite vers un tiers.
- Monitoring du modèle IA (précision de détection des allergènes, latence d'inférence locale) et de l'application (disponibilité, erreurs), avec alerting.
- Suite de tests automatisés (données, modèle, application) intégrée à des pipelines CI/CD (intégration + livraison continues).
- Sécurité applicative conforme aux recommandations OWASP Top 10.
- Accessibilité des interfaces et de la documentation visant le niveau WCAG 2.1 AA / RGAA — point critique ici puisque l'information d'allergène ne doit jamais être communiquée uniquement par une couleur.
- Sobriété numérique : mise en cache des réponses Open Food Facts et des analyses IA pour limiter les appels réseau et les recalculs redondants.

## 5. Environnements et contraintes techniques

- **Développement** : poste local, Docker Compose (Postgres + services), Python 3.11+.
- **Modèle IA local** : nécessite un modèle de taille raisonnable (ex. Llama 3.2 3B ou Mistral 7B quantifié) compatible avec un poste de développement standard, servi par Ollama.
- **Respect des conditions d'usage d'Open Food Facts** : envoi d'un en-tête `User-Agent` identifiant l'application (bonne pratique demandée par OFF), respect des limites de débit raisonnables même en l'absence de clé.
- **Pré-production** : déploiement accessible publiquement pour démonstration (choix d'hébergement détaillé dans `architecture.md`, arbitré en S8-S10) ; le modèle IA local pourra nécessiter une adaptation (modèle plus petit, ou service cloud gratuit de repli) selon les ressources disponibles sur l'hébergement choisi.
- **Contrainte de volumétrie** : projet solo sur 13 semaines à temps plein — le corpus de recettes scrapées et le sous-ensemble de produits importés restent volontairement bornés (échantillons représentatifs), tandis que l'export complet Open Food Facts sert spécifiquement à démontrer la compétence « système big data » via des requêtes analytiques ponctuelles (DuckDB), sans être répliqué intégralement en base applicative.
- **Contrainte budgétaire** : voir section 6.

## 6. Budget

Projet réalisé en solo dans un cadre de formation, sans budget dédié : toutes les sources de données et le service d'IA sont choisis pour être **gratuits et sans inscription**. Seuls d'éventuels frais d'hébergement en pré-production (hors free tier) seraient à arbitrer, et seront identifiés au fil de l'eau dans `docs/00-pilotage/planning.md`.

## 7. Organisation du travail et planification

- Développeur unique, méthode agile (Kanban personnel), sprints hebdomadaires calés sur les semaines du référentiel.
- Board de suivi : [`backlog.md`](backlog.md) (ou GitHub Projects, voir ce même fichier).
- Planning détaillé semaine par semaine : [`docs/00-pilotage/planning.md`](../00-pilotage/planning.md).
- Traçabilité de conformité au référentiel : [`docs/00-pilotage/matrice-competences.md`](../00-pilotage/matrice-competences.md).
- Versionnement Git obligatoire pour tout script/composant produit, avec documentation associée.

## 8. Périmètre et hors périmètre

**Dans le périmètre** : compte utilisateur, profil alimentaire (allergies/régime), recherche de produits et de recettes, détection IA d'incompatibilités, score nutritionnel, suggestions de substitution, historique, monitoring, CI/CD, sécurité, accessibilité.

**Hors périmètre (V1)** : diagnostic médical ou allergologique, recommandation nutritionnelle personnalisée à visée thérapeutique, scan de code-barres par caméra (application mobile native), multi-langue.

## 9. Cadre réglementaire

- **RGPD, article 9** : les allergies/intolérances constituent une donnée de santé, catégorie particulière de données nécessitant un consentement explicite et des mesures de sécurité renforcées. Registre des traitements et procédures de purge à documenter dans `docs/rgpd/`.
- **Règlement européen INCO n° 1169/2011** : référentiel officiel des 14 allergènes à déclaration obligatoire, base du modèle de données (`ALLERGENE`).
- **Réglementation IA** (veille S4) : positionnement de l'application au regard des usages « santé » potentiellement sensibles au sens du règlement européen sur l'IA — à documenter dans la synthèse de veille, avec le disclaimer produit comme mesure de mitigation.
