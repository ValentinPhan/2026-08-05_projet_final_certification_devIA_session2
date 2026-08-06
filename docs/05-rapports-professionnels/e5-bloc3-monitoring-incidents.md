# Rapport professionnel — Épreuve E5 (Cas pratique, C20-C21)

**Projet** : NutriScan IA — assistant de compatibilité alimentaire (allergies/intolérances)
**Bloc** : B3 — Application intégrant le service d'intelligence artificielle
**Semaine** : S11 · **Compétences** : C20 (surveillance d'une application IA), C21 (résolution des incidents techniques)

## 1. Contexte

Ce cas pratique clôt le développement du Bloc 3 en répondant à une question laissée explicitement ouverte depuis le cadrage (US9, S1) : que se passe-t-il réellement, pour l'utilisateur, quand une dépendance du système tombe en panne ? Plutôt que de répondre par une analyse théorique du code, la démarche retenue a été de **provoquer réellement deux pannes** (arrêt effectif de conteneurs/processus) et d'observer le comportement, avant de mettre en place l'outillage de surveillance.

## 2. C20 — Surveillance de l'application

### 2.1 Périmètre retenu

Le monitoring cible le backend applicatif (`app/backend/`, Bloc 3, propriété directe de ce sprint), distinct du suivi qualité du modèle IA (MLflow, Bloc 2, E3) qui répond à un besoin différent — mesurer la fiabilité d'une extraction, pas la santé opérationnelle d'un service.

### 2.2 Journalisation structurée

Format JSON, une ligne par évènement (`inscription`, `connexion_reussie`, `connexion_echouee`, `profil_mis_a_jour`, `historique_ajoute`, `export_rgpd`, `suppression_compte`), pour une ingestion directe par un outil d'agrégation. Règle de confidentialité stricte et vérifiée : aucun secret ni aucune donnée de santé en clair — `profil_mis_a_jour` journalise le *nombre* d'allergènes déclarés, jamais lesquels. Effet secondaire positif documenté : ce log applicatif, externe à la base de données, constitue la seule trace durable d'une suppression de compte, le journal RGPD interne (`traitement_rgpd`) étant lui-même supprimé en cascade avec le compte.

### 2.3 Métriques et tableau de bord

Métriques Prometheus exposées sur `GET /metrics` : requêtes HTTP par route/statut, latence, et compteurs métier (inscriptions, connexions échouées, historique par statut de compatibilité, exports/suppressions RGPD). Tableau de bord Grafana provisionné automatiquement (aucune configuration manuelle), autohébergé via `docker-compose.yml` — cohérent avec le principe zéro-compte tiers du projet.

**Bug réel trouvé et corrigé** : l'image `grafana/grafana:latest` a résolu vers une version dont le rendu du tableau de bord ne s'affichait pas (même un panneau texte sans requête). Diagnostiqué par élimination (source de données fonctionnelle, tableau de bord valide côté serveur, seul le rendu visuel manquait), corrigé en épinglant une version stable connue (`11.1.0`) plutôt que de dépendre d'une étiquette flottante — bonne pratique de reproductibilité au-delà du seul contournement du bug.

**Limite de vérification assumée** : le rendu visuel final du quadrillage de panneaux n'a pas pu être confirmé dans le navigateur automatisé utilisé pour les tests de ce projet (limite de l'outil de test, documentée comme telle). La chaîne de collecte (cible Prometheus active, requêtes réelles exécutées avec succès depuis Grafana *Explore*, provisionnement confirmé via l'API Grafana) a en revanche été intégralement vérifiée.

## 3. C21 — Résolution d'incidents techniques

Deux pannes réellement simulées, chacune ayant révélé de vrais bugs plutôt que de simplement confirmer un comportement déjà correct.

### 3.1 Incident 1 — API Data indisponible

`docker stop` sur le conteneur de l'API Data pendant l'utilisation de l'application. L'API IA, déjà résiliente depuis S6, répond correctement (`502` explicite). Le frontend, en revanche, présentait **quatre bugs réels** :

| Bug | Conséquence |
|---|---|
| Confusion panne/résultat vide (recherche produit, recherche recette, historique) | Un message « aucun résultat » s'affichait après l'erreur déjà montrée, laissant croire à tort à un catalogue ou un historique vide |
| Absence de message sur une erreur HTTP ≥400 renvoyée par le backend | Panne silencieuse pour tout appelant de la fonction d'appel partagée |
| **Mise en cache d'un profil vide en cas d'échec de chargement initial** | Le plus grave : un clic sur « Enregistrer » sans rien cocher aurait **écrasé silencieusement le vrai profil allergène sauvegardé** — donnée de santé perdue par une simple panne transitoire |

Corrections : distinction explicite entre échec (`None`, déjà signalé) et résultat réellement vide ; message d'erreur générique systématique pour toute réponse ≥400 ; page Profil bloquée par un message d'erreur plutôt que de risquer d'écraser une donnée réelle. Vérifié par un cycle panne réelle → constat → conteneur redémarré → constat du retour à la normale.

### 3.2 Incident 2 — Ollama indisponible

Le plus significatif du projet. Avant correctif, l'arrêt réel du processus Ollama pendant une analyse produisait un `500 Internal Server Error` **sans aucun résultat**, y compris pour le filet de sécurité par mots-clés — qui ne nécessite pourtant aucun réseau. Cause : la fonction d'analyse (`ai-service/api_ia/extraction.py`) appelait le modèle *avant* la recherche par mots-clés, sans gestion d'exception ; une erreur de connexion interrompait toute la fonction avant que la partie déterministe ne puisse s'exécuter.

Ce bug annulait, en cas de panne, la garantie même pour laquelle l'architecture hybride avait été conçue en S6 (E2-E3) : ne jamais dépendre uniquement de l'IA pour un allergène explicitement nommé.

**Correction** : recherche par mots-clés calculée en premier, indépendamment du modèle ; appel au modèle encadré par un `try/except` ; en cas d'échec, l'analyse se poursuit en mode dégradé avec un indicateur explicite (`ia_disponible: false`) et une justification claire, jamais un échec silencieux. Le frontend affiche alors un avertissement visible.

**Vérification en cycle complet** :

| Étape | Résultat |
|---|---|
| Avant correctif, Ollama coupé | `500`, aucune détection |
| Après correctif, Ollama toujours coupé | `200`, mode dégradé, allergènes tout de même détectés par mots-clés |
| Ollama redémarré | `200`, fonctionnement normal restauré |

Deux tests automatisés ont été ajoutés pour empêcher toute régression future sur ce point précis.

### 3.3 Une correction inter-blocs assumée

Le correctif de l'incident 2 modifie du code du Bloc 2 (`ai-service/`), déjà validé aux épreuves E2-E3. Choix documenté plutôt que caché : un incident réel ne respecte pas les frontières entre blocs de compétences, et sa découverte n'a été possible qu'en exploitant l'application complète du Bloc 3 — exactement le rôle d'un exercice de gestion d'incident.

## 4. Auto-évaluation et clôture d'US9

Les deux incidents referment explicitement l'US9 (« transparence en cas d'indisponibilité »), restée ouverte depuis le cadrage : dans les deux cas, l'application n'affiche plus jamais un état trompeur, ni un « compatible » par défaut, ni un « aucun résultat » masquant une panne réelle — et informe toujours l'utilisateur de façon claire et accessible.

## 5. Limites assumées et perspectives

- Seules deux dépendances ont été testées en panne (API Data, Ollama) ; une panne de PostgreSQL lui-même n'a pas été simulée dans ce cycle, faute de temps — le comportement attendu (erreurs 500 génériques côté API) suit la même logique mais n'a pas été vérifié empiriquement.
- Les seuils d'alerte proposés dans le tableau de bord (taux d'erreur, latence) sont indicatifs, faute de données de production réelles sur lesquelles les calibrer.

## 6. Conclusion

Ce dernier cas pratique du Bloc 3 illustre, une fois de plus, la méthodologie suivie sur l'ensemble du projet : provoquer une panne réelle plutôt que de la supposer gérée est ce qui a révélé le bug le plus critique de tout le développement — la perte de la garantie de sécurité de l'architecture hybride IA + mots-clés en cas de panne du modèle. Sa correction, vérifiée par un cycle complet panne/rétablissement et couverte par des tests de non-régression, referme ce cas pratique et, avec lui, l'ensemble du Bloc 3.
