# Rapport professionnel — Épreuve E4 (Mise en situation, C14-C19)

**Projet** : NutriScan IA — assistant de compatibilité alimentaire (allergies/intolérances)
**Bloc** : B3 — Application intégrant le service d'intelligence artificielle
**Semaines** : S1 (cadrage), S9 (application), S10 (CI/CD) · **Compétences** : C14 (analyse du besoin), C15 (cadre technique), C16 (coordination de la réalisation), C17 (développement des composants), C18 (CI), C19 (CD)

## Sommaire

1. Contexte
2. C14 — Analyse du besoin
3. C15 — Cadre technique de l'application
4. C16 — Coordination de la réalisation technique
5. C17 — Développement des composants techniques et interfaces
6. C18 — Intégration continue de l'application
7. C19 — Livraison continue de l'application
8. Grille d'auto-évaluation par compétence
9. Synthèse transversale
10. Limites assumées et perspectives
11. Conclusion

---

## 1. Contexte

Le Bloc 3 est le point de convergence du projet : il transforme les données du Bloc 1 et le service d'IA du Bloc 2 en une application utilisable, avec un compte utilisateur réel et une persistance effective. Particularité de calendrier assumée : les compétences de cadrage (C14-C16) sont réalisées en S1, avant tout code, tandis que la réalisation (C17) et son industrialisation (C18-C19) n'interviennent qu'en S9-S10, une fois les Blocs 1 et 2 achevés et éprouvés. Ce rapport suit cet ordre chronologique réel plutôt qu'un ordre purement thématique, parce que le décalage entre cadrage et réalisation a lui-même produit des enseignements (voir §9).

## 2. C14 — Analyse du besoin

### 2.1 Cahier des charges

Le besoin métier est posé sans ambiguïté dès le cadrage : un consommateur allergique doit aujourd'hui lire manuellement chaque liste d'ingrédients, exercice fastidieux et source d'erreur, en particulier sur des recettes qui ne mentionnent pas explicitement les allergènes. NutriScan IA automatise cette vérification via un profil alimentaire déclaré, une recherche de produit ou de recette, et une analyse de compatibilité générée par IA, complétée d'un score nutritionnel et de substitutions.

Le cahier des charges pose explicitement, dès la section 1, la contrainte fondatrice de tout le projet : **aucune source de donnée ni le service d'IA ne nécessite de compte ou de clé API**. Cette contrainte n'est pas anecdotique — elle est la raison directe du choix du sujet lui-même (un sujet initial envisagé, orienté recherche d'emploi, impliquait la création de comptes développeur sur des API tierces, et a été abandonné pour cette raison avant même le début du cadrage). Elle structure ensuite chaque décision technique du projet, du choix d'Ollama (E2) jusqu'au choix de ne pas héberger l'application chez un tiers en pré-production (§7 de ce rapport).

Le périmètre est posé avec un hors-périmètre explicite (diagnostic médical, recommandation thérapeutique, scan caméra, multi-langue) — délimitation nécessaire pour un projet solo de 13 semaines, et qui évite de faire dériver l'ambition fonctionnelle au fil de l'eau.

### 2.2 User stories et modélisation

Neuf user stories (US1-US9) couvrent le parcours complet : inscription/connexion sécurisées, définition du profil alimentaire, recherche produit/recette, alerte de compatibilité, score nutritionnel, historique, maîtrise des données personnelles (RGPD), et transparence en cas d'indisponibilité. Chacune est assortie de critères d'acceptation **fonctionnels et d'accessibilité** dès leur rédaction — pas ajoutés après coup — par exemple : « le statut de compatibilité n'est jamais communiqué uniquement par la couleur » (US4), directement issu du constat que l'information d'allergène a un enjeu de sécurité et non seulement d'ergonomie.

Le modèle de données (Merise, MCD → MLD) anticipe dès S1 les entités nécessaires à ces neuf user stories, y compris celles qui ne seront implémentées qu'en S9 (`UTILISATEUR`, `ANALYSE_COMPATIBILITE`, `TRAITEMENT_RGPD`) — voir rapport E1 pour le détail du modèle, commun aux Blocs 1 et 3.

## 3. C15 — Cadre technique de l'application

### 3.1 Architecture retenue

Trois composants faiblement couplés, un par bloc de compétences, communiquant exclusivement par API REST — **aucun composant n'accède directement à la base d'un autre**. Ce principe, posé en S1, a été rappelé et respecté à chaque ajout ultérieur : quand le backend applicatif (`app/backend/`) a été construit en S9 pour porter les données personnelles, il a été conçu comme un service supplémentaire consommant la même base PostgreSQL que l'API Data mais sur des tables strictement séparées, jamais comme un accès direct de l'application à la base du Bloc 1.

### 3.2 Sécurité et accessibilité posées dès le cadrage

Le cadre technique fixe, avant tout code, les exigences qui seront vérifiées bien plus tard : authentification JWT entre les composants, chiffrement au repos de la donnée de santé, secrets exclusivement en variables d'environnement, recommandations OWASP, HTTPS en pré-production, et objectif WCAG 2.1 AA / RGAA renforcé sur les alertes allergènes. Le fait que ces exigences soient écrites *avant* le développement plutôt que constatées après coup a un effet mesurable : les vérifications de sécurité et d'accessibilité conduites en S9-S11 (voir §5 et rapport E5) consistent à *contrôler* des exigences déjà posées, pas à les découvrir.

### 3.3 Une décision d'architecture révisée en connaissance de cause

Point de rigueur méthodologique à souligner : l'architecture initiale de S1 prévoyait un hébergement de pré-production chez un tiers gratuit (Neon, Render...). Cette option a été **explicitement reconsidérée en S10** lorsque sa mise en œuvre a nécessité de créer un compte externe — en contradiction directe avec le principe zéro-compte posé dans ce même document dès la section 2. Plutôt que d'ignorer la contradiction ou de la trancher silencieusement, la décision a été explicitement discutée avec le porteur du projet et actée : la livraison continue s'arrête à la publication d'images Docker versionnées sur GitHub Container Registry, sans mise en ligne effective chez un hébergeur (voir §7). Le document d'architecture a été mis à jour en conséquence plutôt que laissé incohérent avec la pratique réelle.

## 4. C16 — Coordination de la réalisation technique

Projet solo : la coordination agile est portée par le développeur lui-même, avec des rituels explicites plutôt qu'informels — revue hebdomadaire de la matrice de compétences en début de semaine, mise à jour du board en fin de semaine (`docs/01-cadrage/backlog.md`), et une règle de traçabilité stricte : chaque tâche terminée est reliée à un commit Git et, si applicable, à la compétence qu'elle satisfait.

Le board est tenu à jour au fil de l'eau — les cartes des sprints S9 à S13 ont été ajoutées *au moment où elles ont été réalisées*, pas toutes d'avance, pour que le board reste un reflet honnête de l'avancement réel plutôt qu'une planification figée. Cette discipline a directement permis, semaine après semaine, de documenter les bugs réels trouvés et corrigés (voir §5, §8) au fur et à mesure plutôt que de manière rétrospective approximative.

## 5. C17 — Développement des composants techniques et interfaces

### 5.1 Refonte architecturale du Bloc 3 en S9

L'architecture de S1 décrivait l'application comme un unique bloc « Streamlit (front + back) ». En construisant réellement la persistance en S9, un découpage plus fin s'est imposé pour rester cohérent avec le principe déjà appliqué aux deux autres blocs : un frontend ne se connecte jamais directement à une base de données, il appelle une API. `app/backend/` (nouveau service FastAPI) possède et est seul à écrire les tables de données personnelles (`utilisateur`, `utilisateur_allergene`, `analyse_compatibilite`, `traitement_rgpd`, modélisées dès S1 mais jamais écrites avant cette semaine) ; `app/frontend/main.py` ne se connecte à aucune base et appelle les trois API du système (Data, IA, backend applicatif) de façon strictement identique.

### 5.2 Fonctionnalités livrées

- **US1-US2** : inscription/connexion avec mot de passe haché (bcrypt), deux consentements RGPD distincts et non pré-cochés, profil allergène persistant et chiffré au repos (`pgcrypto`).
- **US3-US5** : recherche de produits et recettes, analyse de compatibilité réelle via l'API IA.
- **US6** : score nutritionnel détaillé — nécessitant un enrichissement rétroactif du Bloc 1 (persistance des nutriments Open Food Facts déjà collectés mais jamais stockés ; rapprochement heuristique ingrédient ↔ Ciqual, 80 % de couverture réelle mesurée sur le corpus de recettes). Ce retour vers un bloc déjà validé, plutôt qu'un contournement côté Bloc 3, est documenté comme un choix assumé : un score nutritionnel qui afficherait des valeurs inventées serait pire qu'une fonctionnalité incomplète.
- **US7-US8** : historique des analyses, export JSON et suppression de compte à double confirmation (case à cocher + ressaisie de l'email) — droits RGPD réellement exécutables en libre-service, pas seulement décrits dans un registre.

### 5.3 Sécurité (OWASP) et accessibilité, vérifiées et non simplement déclarées

- Mots de passe hachés (bcrypt), jamais en clair.
- Anti-énumération de comptes : `/auth/connexion` renvoie le même code et le même message qu'un email soit inconnu ou le mot de passe incorrect, avec une vérification bcrypt même sur un hash factice pour ne pas révéler l'existence d'un compte par le temps de réponse.
- Anti-bruteforce : fenêtre glissante en mémoire, 5 échecs / 15 min par email.
- Jeton de session dédié (`APP_JWT_SECRET_KEY`), distinct du jeton service-à-service (`JWT_SECRET_KEY`) : un jeton de session utilisateur compromis ne peut jamais être rejoué comme jeton de service.
- Accessibilité vérifiée dans le navigateur, pas seulement supposée conforme au code : une case à cocher native et individuellement étiquetée par allergène (US2), jamais de statut porté par la seule couleur (US4), historique restitué en table HTML sémantique plutôt qu'en grille interactive.

### 5.4 Deux bugs réels trouvés en testant, révélateurs de la méthode suivie

- **`passlib` incompatible avec les versions récentes de `bcrypt`** : découvert au tout premier démarrage du service (`ValueError: password cannot be longer than 72 bytes`), corrigé en abandonnant `passlib` pour un usage direct de `bcrypt`, plus simple et sans cette couche d'abstraction devenue inutile.
- **Widget conditionnel invisible dans un formulaire Streamlit** : le sélecteur de niveau d'allergène, censé apparaître dès qu'une case est cochée, restait invisible tant que le formulaire n'était pas déjà soumis — Streamlit ne relance le script qu'à la soumission d'un `st.form`, jamais à l'interaction avec un widget qu'il contient. Corrigé en sortant le profil du formulaire, revérifié dans le navigateur.

## 6. C18 — Intégration continue de l'application

`.github/workflows/ci-app.yml` : analyse statique (`ruff`, configuration excluant explicitement les règles de modernisation qui casseraient la compatibilité Python 3.9 des modèles Pydantic) puis tests du backend contre un **vrai service container PostgreSQL** — schéma appliqué et jeu de données minimal semé pour que les tests d'historique/export s'exécutent réellement plutôt que d'être ignorés faute de données.

Vérification locale menée avec plus de rigueur que ne l'aurait permis `act` (indisponible dans l'environnement de développement à cette période) : simulation complète du job dans un conteneur PostgreSQL jetable, reproduisant fidèlement un environnement CI propre. Cette précaution n'a pas empêché un vrai run GitHub Actions d'échouer : la version de Starlette résolue en CI (plus récente que celle du poste de développement) exige un nouveau paquet (`httpx2`) pour son client de test, absent de `requirements.txt`. Corrigé, puis run suivant réussi en 43 secondes (lint 9 s, tests 34 s) — même schéma de découverte que pour la CI/CD MLOps du Bloc 2 (E3) : un décalage de version entre poste local et environnement CI révèle un problème qu'aucune relecture n'aurait trouvé.

## 7. C19 — Livraison continue de l'application

### 7.1 Portée assumée du « déploiement pré-production »

Décision documentée en amont de l'implémentation (§3.3) : la CD publie des images Docker versionnées sur GitHub Container Registry (`nutriscan-app-backend`, `nutriscan-app-frontend`), avec `GITHUB_TOKEN` intégré et zéro nouveau compte, plutôt que de déployer effectivement chez un hébergeur tiers. Ce choix satisfait la partie « build Docker » de la compétence et livre un artefact réellement déployable (`docker pull` + `docker run` sur n'importe quel hôte Docker), sans compromettre le principe zéro-compte du projet.

### 7.2 Enchaînement CI → CD et vérification réelle du gating

Déclencheur `workflow_run` plutôt qu'un simple `push` dupliqué : la CD ne se déclenche qu'après le succès de la CI sur `main`, ce qui matérialise concrètement la raison de séparer les deux fichiers plutôt que de tout enchaîner aveuglément. Ce gating a été vérifié en conditions réelles, pas seulement supposé fonctionner d'après la configuration : un premier déclenchement (après un run de CI en échec) a été correctement marqué `skipped` par GitHub Actions ; un second déclenchement (après le run de CI corrigé) a réussi en 1 min 24 s, avec les deux images confirmées présentes sur la page *Packages* du compte GitHub.

### 7.3 Traçabilité du commit publié

Point technique documenté : sur un déclenchement `workflow_run`, `github.sha` pointe par défaut sur l'état du dépôt au moment de l'évènement CD, pas nécessairement sur le commit réellement testé par le run CI déclencheur. Le job checkout donc explicitement `github.event.workflow_run.head_sha`, pour que l'image publiée corresponde toujours exactement au commit qui a été validé par la CI.

## 8. Grille d'auto-évaluation par compétence

| Compétence | Ce qui était attendu | Constat | Point de vigilance identifié a posteriori |
|---|---|---|---|
| **C14** — Analyse du besoin | Cahier des charges et user stories exploitables tout au long du projet, pas un exercice isolé | Chaque user story reprise et implémentée effectivement en S9 ; le hors-périmètre posé en S1 (pas de diagnostic médical, pas de scan caméra) a été respecté sans dérive jusqu'à la fin | US9 (transparence en cas d'indisponibilité) est restée non implémentée pendant 10 semaines avant d'être close en S11 — un suivi plus actif de l'état de chaque user story dans le board aurait permis de la traiter plus tôt, indépendamment de l'exercice d'incident qui l'a finalement close |
| **C15** — Cadre technique | Une architecture qui tient sur la durée du projet | Le principe « API uniquement entre composants » posé en S1 est resté vrai jusqu'au dernier composant créé (S9) | Le stockage (« pas de base propre » pour l'app) a dû être précisé/nuancé en S9 quand `app/backend/` a été créé — la formulation initiale n'anticipait pas complètement ce découpage, corrigée a posteriori dans le document plutôt que laissée ambiguë |
| **C16** — Coordination agile | Un pilotage réel, pas un board figé en début de projet | Board mis à jour semaine par semaine, traçabilité systématique tâche → commit → compétence | Projet solo : la coordination n'a pas été mise à l'épreuve d'une vraie négociation d'équipe (priorisation contradictoire entre plusieurs personnes) — limite structurelle du format solo, pas un défaut d'exécution |
| **C17** — Développement des composants | Une application fonctionnelle, sécurisée, accessible, testée | Backend + frontend livrés, testés en conditions réelles (navigateur), 33 tests automatisés, deux bugs réels trouvés et corrigés | La couverture de tests automatisés du frontend Streamlit reste plus faible que celle du backend (l'essentiel de la vérification du frontend est manuelle, dans le navigateur) — assumé car les outils de test automatisé de Streamlit sont moins matures que ceux d'une API REST, mais reste une dépendance à la discipline de test manuel |
| **C18** — Intégration continue | Une CI qui teste réellement, pas seulement qui s'exécute sans erreur | Tests contre un vrai service container PostgreSQL, pas des mocks ; bug réel trouvé et corrigé dès le premier run | Le frontend n'a pas de job de CI dédié (pas de tests automatisés à exécuter) — cohérent avec la limite documentée pour C17, mais un lint minimal du frontend aurait pu être ajouté à moindre coût |
| **C19** — Livraison continue | Un processus de publication fiable et vérifié | Gating CI→CD vérifié en conditions réelles (un run `skipped`, un run réussi), traçabilité du commit publié | Le déploiement s'arrête à la publication d'images Docker, pas à une mise en ligne effective — choix assumé et documenté (§7.1), mais qui laisse la démonstration finale dépendante d'un environnement local plutôt que d'une URL publique |

## 9. Synthèse transversale

Le fil conducteur des six compétences de ce bloc est la cohérence maintenue entre la vision posée en S1 et sa réalisation huit semaines plus tard : le principe « une API, jamais un accès direct à la base d'un autre composant » est respecté à l'identique quand `app/backend/` est créé en S9 ; le principe zéro-compte externe, posé dans le cahier des charges dès la section 1, est celui qui a explicitement tranché le débat sur l'hébergement de pré-production en S10, plutôt que d'être oublié en cours de route.

Le cadrage (C14-C16) n'a donc pas été un exercice isolé produit en début de projet puis jamais reconsulté : il a servi de référence active pour arbitrer une décision réelle sept mois de calendrier de formation plus tard (au sens du planning), ce qui en constitue la meilleure validation possible.

## 10. Limites assumées et perspectives

- Le décalage de plusieurs semaines entre le cadrage (S1) et la réalisation de l'application (S9) a un revers : une donnée nécessaire au score nutritionnel (US6) n'avait pas été anticipée dans le pipeline d'import du Bloc 1, obligeant un retour en arrière documenté plutôt qu'un oubli silencieux (voir §5.2). Un prochain projet gagnerait à relire le cahier des charges juste avant chaque nouveau développement de fonctionnalité, pas seulement au moment du cadrage initial.
- Le rendu visuel final d'un tableau de bord de monitoring (Grafana, compétence C20, voir rapport E5) n'a pas pu être confirmé dans l'environnement de test automatisé utilisé pour ce projet — limite d'outillage documentée plutôt que masquée, sans impact sur la chaîne de collecte elle-même, vérifiée indépendamment.
- Le déploiement pré-production réel (au-delà de la publication d'images Docker) reste une étape ouverte, explicitement documentée comme un choix de reporter plutôt que de compromettre le principe zéro-compte du projet.

## 11. Conclusion

Le Bloc 3, dans son volet cadrage-réalisation-industrialisation (C14-C19), démontre qu'une architecture pensée dès le premier jour peut rester la référence active d'un projet qui s'étend sur plusieurs mois, y compris pour trancher des décisions que le cadrage initial n'avait pas explicitement anticipées. L'application livrée est fonctionnelle de bout en bout, testée en conditions réelles, sécurisée selon les principes posés dès S1, et intégrée dans une chaîne de livraison continue vérifiée sur l'infrastructure réelle de GitHub.
