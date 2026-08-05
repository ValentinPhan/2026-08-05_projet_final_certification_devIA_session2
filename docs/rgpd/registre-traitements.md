# Registre des traitements de données personnelles — NutriScan IA

Registre tenu au sens de l'article 30 du RGPD, couvrant les traitements mis en œuvre par l'application. Projet pédagogique de certification : le « responsable de traitement » désigne le porteur du projet en tant qu'éditeur fictif du service.

- **Responsable de traitement** : porteur du projet NutriScan IA (voir [cahier des charges](../01-cadrage/cahier-des-charges.md)).
- **DPO** : non désigné (effectif hors seuil légal pour un projet pédagogique) ; à mentionner explicitement dans le rapport comme un point de vigilance en cas de mise en production réelle.
- **Sous-traitants** : aucun à ce stade (S3). Un hébergeur de pré-production sera choisi en S8-S10 (voir [architecture.md](../01-cadrage/architecture.md)) et ajouté ici avec sa localisation (exigence de transfert hors UE à vérifier).
- **Transferts hors UE** : aucun. Le service d'IA (bloc 2) est exécuté en local (Ollama) — voir [benchmark-services-ia.md](../03-bloc2-ia/benchmark-services-ia.md) — ce qui exclut par construction tout transfert de donnée personnelle vers un service tiers.

## Traitement 1 — Gestion du compte utilisateur

| Champ | Détail |
|---|---|
| Finalité | Authentifier l'utilisateur et lui donner accès à son espace personnel |
| Données traitées | Email, mot de passe (haché), date d'inscription |
| Personnes concernées | Utilisateurs inscrits de l'application |
| Base légale | Exécution du contrat (conditions d'utilisation du service) |
| Destinataires | Équipe technique du projet ; aucun tiers |
| Durée de conservation | Durée de vie du compte + 30 jours après une demande de suppression (délai de rétractation), puis suppression définitive |
| Mesures de sécurité | Mot de passe haché (jamais stocké en clair), connexion chiffrée (HTTPS), accès à la base restreint |
| Table(s) associée(s) | `utilisateur` |

## Traitement 2 — Profil alimentaire (allergies, intolérances, régime)

| Champ | Détail |
|---|---|
| Finalité | Détecter les incompatibilités entre le profil de l'utilisateur et un produit/une recette |
| Données traitées | Type d'allergène/régime déclaré, niveau (allergie / intolérance / préférence) |
| **Catégorie particulière** | **Oui — donnée de santé au sens de l'article 9 du RGPD** |
| Personnes concernées | Utilisateurs ayant renseigné un profil alimentaire |
| Base légale | **Consentement explicite et distinct** (case à cocher dédiée, séparée du consentement RGPD général — voir [user-stories.md, US1](../01-cadrage/user-stories.md#us1--inscription-et-connexion-sécurisées)) |
| Destinataires | Aucun tiers. Traitement IA réalisé **localement** (Ollama) : la donnée ne quitte jamais l'infrastructure applicative |
| Durée de conservation | Jusqu'à modification/suppression par l'utilisateur, ou suppression du compte |
| Mesures de sécurité | **Chiffrement au repos** (colonne `niveau_chiffre`, `pgcrypto`, clé applicative hors base — voir [schema.sql](../../data-pipeline/db/schema.sql)), accès restreint, aucune sortie réseau vers un service tiers |
| Table(s) associée(s) | `utilisateur_allergene` |

## Traitement 3 — Historique des analyses de compatibilité

| Champ | Détail |
|---|---|
| Finalité | Permettre à l'utilisateur de retrouver ses recherches passées (US7) |
| Données traitées | Produit/recette consulté, résultat de compatibilité, date |
| Personnes concernées | Utilisateurs ayant réalisé au moins une analyse |
| Base légale | Intérêt légitime (fonctionnalité attendue du service) |
| Destinataires | Aucun tiers |
| Durée de conservation | 24 mois à compter de la dernière connexion, puis purge automatique (voir [procedures-tri.md](procedures-tri.md)) ; suppression immédiate avec le compte |
| Mesures de sécurité | Accès restreint à l'utilisateur concerné (isolation applicative par `id_utilisateur`) |
| Table(s) associée(s) | `analyse_compatibilite` |

## Traitement 4 — Journal de traçabilité RGPD (accountability)

| Champ | Détail |
|---|---|
| Finalité | Prouver la conformité des traitements réalisés (principe de responsabilité, art. 5.2 RGPD) |
| Données traitées | Type de traitement effectué, finalité, indicateur de donnée de santé, date |
| Base légale | Obligation légale (accountability) |
| Durée de conservation | Durée de vie du compte concerné |
| Table(s) associée(s) | `traitement_rgpd` |

## Droits des personnes concernées

- **Droit d'accès / de rectification** : depuis l'espace personnel (profil, historique).
- **Droit à l'effacement** : US8 — suppression de compte avec double confirmation, cascade sur `utilisateur_allergene`, `analyse_compatibilite` et `traitement_rgpd` (contraintes `ON DELETE CASCADE`, voir schema.sql).
- **Droit à la portabilité** : export des données du compte (à implémenter au niveau de l'application, Bloc 3).
- **Délai de réponse** : 1 mois maximum à compter de la demande (art. 12 RGPD).
