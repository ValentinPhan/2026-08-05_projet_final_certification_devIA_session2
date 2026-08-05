# Procédures de tri et de purge des données personnelles

Complète le [registre des traitements](registre-traitements.md) : décrit comment chaque durée de conservation annoncée est réellement appliquée.

## 1. Suppression de compte (US8)

- Déclenchement : demande explicite de l'utilisateur, confirmée deux fois (voir critère d'acceptation US8).
- Effet immédiat : la ligne `utilisateur` est supprimée après un délai de rétractation de 30 jours (marqué via `date_suppression_demandee`).
- Effet en cascade (géré par les contraintes `ON DELETE CASCADE` du schéma, voir [schema.sql](../../data-pipeline/db/schema.sql)) : suppression automatique des lignes associées dans `utilisateur_allergene`, `analyse_compatibilite` et `traitement_rgpd`. Aucune purge manuelle multi-tables n'est nécessaire : c'est la base de données elle-même qui garantit qu'aucune donnée personnelle ne peut survivre orpheline à la suppression du compte.
- Une ligne est ajoutée dans `traitement_rgpd` (`type_traitement = 'suppression_compte'`) **avant** l'exécution de la suppression, pour que la preuve de la demande survive à la suppression des données elle-même (obligation de traçabilité, traitement 4 du registre).

## 2. Purge de l'historique d'analyses (traitement 3 du registre)

- Règle annoncée : 24 mois d'inactivité du compte.
- Mise en œuvre prévue (Bloc 3, tâche planifiée) : une requête programmée (ex. tâche CI/CD planifiée ou job applicatif) supprime les lignes `analyse_compatibilite` dont `date_analyse` dépasse 24 mois **et** dont l'utilisateur associé ne s'est pas connecté depuis autant de temps. Requête de référence :

```sql
DELETE FROM analyse_compatibilite
WHERE date_analyse < now() - INTERVAL '24 months';
```

- Cette purge est un traitement à part entière : elle doit elle aussi être journalisée dans `traitement_rgpd` (`type_traitement = 'purge_historique'`, sans `id_utilisateur` unique puisqu'elle s'applique en masse — une ligne de synthèse suffit, horodatée).

## 3. Comptes inactifs sans demande de suppression

- Un compte n'ayant jamais servi à réaliser d'analyse et inactif depuis plus de 36 mois est considéré comme abandonné.
- Procédure : notification par email (si l'adresse reste valide) avant purge, puis application de la procédure de suppression de compte (section 1) si aucune réaction dans un délai de 30 jours.
- Cette règle sera implémentée comme tâche planifiée au moment du développement applicatif (Bloc 3, S9) ; elle est documentée ici dès S3 pour que le registre des traitements soit complet dès le cadrage de la base de données.

## 4. Minimisation dès la collecte (Bloc 1)

- Le pipeline de collecte ([`data-pipeline/extract/`](../../data-pipeline/extract)) ne traite que des données publiques de produits/recettes : aucune donnée personnelle n'y transite.
- Les seules données personnelles de l'application sont celles créées directement par l'utilisateur (compte, profil, historique) — elles n'existent dans aucun jeu de données brut ou intermédiaire du Bloc 1.
