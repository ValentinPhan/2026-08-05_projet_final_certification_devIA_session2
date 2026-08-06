# Rapport professionnel — Épreuve E2 (Cas pratique, C6-C8)

**Projet** : NutriScan IA — assistant de compatibilité alimentaire (allergies/intolérances)
**Bloc** : B2 — Intégration d'un service d'intelligence artificielle
**Semaines** : S4-S5 · **Compétences** : C6 (veille technique et réglementaire), C7 (identification et comparaison de services IA), C8 (paramétrage et test de faisabilité d'un service IA)

## Sommaire

1. Contexte et reformulation du besoin
2. C6 — Veille technique et réglementaire
3. C7 — Benchmark des services d'intelligence artificielle
4. C8 — POC du service IA retenu
5. Grille d'auto-évaluation par compétence
6. Synthèse transversale
7. Limites assumées et perspectives
8. Conclusion

---

## 1. Contexte et reformulation du besoin

NutriScan IA a pour cœur de fonctionnalité de confronter la liste d'ingrédients d'un produit ou d'une recette au profil allergène d'un utilisateur, et de rendre un verdict de compatibilité explicable. Cette confrontation nécessite d'**extraire les allergènes et ingrédients pertinents d'un texte libre**, écrit dans un registre et une langue non maîtrisés à l'avance (français, anglais, parfois allemand pour des produits importés — cas réellement rencontré, voir §4). Le Bloc 2 couvre l'ensemble du chemin qui va de « quel service utiliser pour cette tâche » à « ce service fonctionne-t-il, et avec quelle fiabilité ».

Cette réflexion s'inscrit dans un cadre de contraintes posées dès le cadrage du projet (S1) et rappelées ici parce qu'elles structurent chacune des trois compétences de ce bloc :

- **Budget nul** — aucun service facturé à l'usage ne peut être une solution par défaut.
- **Aucune création de compte** — contrainte explicite, à l'origine même du choix du sujet NutriScan IA (le sujet initialement envisagé impliquait la création de comptes développeur sur des API tierces, écarté pour cette raison).
- **Confidentialité par conception** — le résultat de l'extraction est ensuite croisé avec une donnée de santé au sens de l'article 9 du RGPD (le profil allergène). Minimiser le nombre de tiers dans la chaîne est un principe de précaution, même si ce croisement a lieu en dehors de l'appel IA lui-même.
- **Reproductibilité** — la solution doit fonctionner sur un poste de développement standard, sans dépendre d'un abonnement dont les conditions pourraient changer.

Ces quatre contraintes ne sont pas de simples préférences : elles éliminent d'emblée une partie substantielle du marché (tous les services cloud à authentification par clé API), ce qui rend la phase de veille et de benchmark d'autant plus déterminante pour ne pas se retrouver, en S5-S6, sans solution viable.

## 2. C6 — Veille technique et réglementaire

### 2.1 Thématiques retenues

Deux axes, choisis parce que directement mobilisés par le projet plutôt que génériques :

- **Réglementaire** : le traitement des données de santé (profil allergène, RGPD article 9) et la réglementation de la sécurité alimentaire relative aux allergènes (règlement UE INCO 1169/2011, qui définit précisément les 14 allergènes à déclaration obligatoire repris comme référentiel de l'application).
- **Technique** : l'état de l'art des modèles d'IA exécutables en local, écosystème qui évolue vite (nouvelles versions, nouveaux modèles compacts) et qu'il est nécessaire de suivre pour ne pas figer un choix sur une information périmée.

### 2.2 Organisation et méthodologie

La veille est portée en solo (projet individuel), avec une organisation volontairement légère mais régulière plutôt qu'un outil lourd sous-utilisé :

- Un **créneau hebdomadaire d'une heure**, aligné sur le rituel agile déjà en place (revue de sprint, voir `docs/01-cadrage/backlog.md`), complété d'une vérification rapide de 10 minutes en milieu de semaine sur les seules sources techniques (plus volatiles que les sources réglementaires).
- La synthèse est journalisée dans un document versionné (`docs/03-bloc2-ia/veille.md`) plutôt que gardée informelle — choix qui a directement profité au projet : chaque « action » identifiée dans la synthèse a un lien de traçabilité vers la semaine où elle a été mise en œuvre (voir §2.4).

### 2.3 Outils de collecte, sources retenues et fiabilité

| Besoin | Outil retenu | Justification |
|---|---|---|
| Agrégation des flux | Script Python (`ai-service/veille/aggregate_veille.py`, bibliothèque `feedparser`) sur des flux RSS/Atom publics | Gratuit, sans compte ni clé, reproductible et versionné avec le projet — cohérent avec la contrainte budgétaire (0 €) |
| Partage des synthèses | Document Markdown versionné dans le dépôt Git | Accessible sans outil propriétaire, structuré par titres hiérarchiques, lisible par un lecteur d'écran |

Alternative explicitement écartée : un agrégateur grand public (Feedly, Inoreader) aurait offert une interface plus riche, mais nécessite la création d'un compte — rejeté pour rester cohérent avec la contrainte fondatrice du projet, y compris pour un outil de veille qui n'aurait pourtant qu'un usage interne.

Quatre sources ont été retenues, chacune évaluée explicitement sur un critère de fiabilité (auteur identifiable, procédure de publication tracée) plutôt que sur leur seule popularité :

| Source | Thème | Évaluation de fiabilité |
|---|---|---|
| CNIL — Actualités | Réglementaire | Autorité administrative indépendante française, publications datées et sourcées, aucun intérêt commercial |
| EFSA — News | Réglementaire | Agence de l'Union européenne, avis rendus par des panels d'experts nommés, procédure de publication tracée |
| Ollama — Releases (GitHub) | Technique | Dépôt officiel du projet (organisation vérifiée), changelog détaillé et daté à chaque version |
| Hugging Face — Blog | Technique | Plateforme de référence du secteur, auteurs identifiés par organisation, contenu daté |

Des agrégateurs d'actualité tech grand public ont été examinés puis écartés : le niveau d'expertise et l'identité de l'auteur n'y sont pas systématiquement vérifiables — un critère jugé prioritaire dès lors que la veille réglementaire influence directement des choix de conformité RGPD.

### 2.4 Synthèse et actions concrètes tirées de la veille

La veille n'a de valeur que si elle débouche sur des décisions traçables. Extraits de la synthèse de la semaine du 2026-08-05 (méthodologie reproductible en relançant le script d'agrégation) :

**Réglementaire** — la CNIL publie deux ressources sur les méthodologies de référence santé (MR-001/MR-003) et un téléservice pour les demandes d'autorisation « santé et recherche ». Ces méthodologies encadrent le traitement de données de santé à des fins d'étude : sans application immédiate pour un projet pédagogique, la référence a été notée dans le registre des traitements RGPD comme point de vigilance explicite pour une éventuelle mise en production réelle — plutôt que découverte tardivement si le projet devait un jour sortir du cadre scolaire.

L'EFSA publie des avis sur des « novel foods » rendus par le panel NDA (*Nutrition, Novel Foods and Food Allergens*) : confirmation que cette source reste la bonne autorité à surveiller sur la durée du projet pour toute évolution du référentiel des 14 allergènes, même sans changement direct cette semaine-là.

**Technique** — trois constats ont eu un effet direct sur les choix d'implémentation ultérieurs :

1. Ollama a publié 4 versions en dix jours et aligné le format de streaming de son endpoint `/v1/chat/completions` sur le format natif d'OpenAI. **Décision retenue pour S6** : utiliser directement le client Python `openai` standard plutôt qu'un client HTTP maison — ce choix a effectivement simplifié l'intégration de l'API IA (`ai-service/api_ia/`) et s'est révélé payant sur la durée (compatibilité conservée à travers toutes les mises à jour ultérieures d'Ollama observées sur le projet).
2. Un article Hugging Face présente un modèle compact conçu pour l'inférence locale/embarquée (LFM2.5-2.6B) : noté comme alternative de repli à évaluer en S5 si le modèle initialement pressenti se révélait trop lourd — l'alternative n'a finalement pas été nécessaire (voir §4), mais avoir identifié un plan B a réduit le risque du POC.
3. Un article relatant une intrusion technique visant un agent d'un « frontier lab » a servi de rappel concret pour la conception sécurité (OWASP) de l'API IA développée en S6 : ne jamais exposer directement les capacités d'exécution du modèle sans validation des entrées côté API — principe effectivement appliqué (validation Pydantic stricte, limitation de débit, voir rapport E3).

### 2.5 Accessibilité de la diffusion

Le document de veille respecte les recommandations RGAA/WCAG applicables à un contenu texte : titres hiérarchiques structurant la navigation, tableaux à en-têtes explicites, liens explicites (jamais de « cliquez ici »), aucune information portée uniquement par la couleur.

## 3. C7 — Benchmark des services d'intelligence artificielle

### 3.1 Services étudiés et méthode de sélection

Quatre services ont été étudiés en détail (Ollama, OpenAI API, Mistral API, Groq) ; trois autres ont été identifiés puis explicitement écartés de l'étude approfondie, avec la raison consignée plutôt que simplement omis :

| Service | Raison de l'exclusion |
|---|---|
| Hugging Face Inference API | Redondant avec Ollama pour l'exécution de modèles open-source ; n'apporte pas d'avantage suffisant pour justifier la création d'un compte que Ollama permet d'éviter |
| LM Studio | Alternative locale équivalente à Ollama sur les critères déterminants (gratuit, sans compte, exécution locale) ; retenue comme **solution de repli documentée** plutôt qu'étudiée en profondeur, une fois Ollama confirmé installé et fonctionnel |
| Azure AI Foundry / AWS Bedrock | Offres cloud entreprise écartées d'emblée : nécessitent un compte facturé et sont surdimensionnées pour l'échelle d'un projet pédagogique |

### 3.2 Grille de comparaison

| Critère | **Ollama** (local) | OpenAI API | Mistral API | Groq |
|---|---|---|---|---|
| Adéquation fonctionnelle | Bonne pour l'extraction d'entités avec des modèles 3B-8B ; qualité à confirmer par le POC | Excellente, multilingue, très documentée | Bonne, spécialisé multilingue FR/EN | Bonne (modèles open-source hébergés), débit très élevé |
| Contraintes techniques | RAM/CPU suffisants (8-16 Go recommandés), GPU optionnel ; **déjà installé et fonctionnel** sur le poste de développement | Compte + clé API requis | Compte + clé API requis | Compte + clé API requis |
| Éco-responsabilité | Aucun rapport de cycle de vie publié (logiciel, pas service géré) ; pas de nouvelle infrastructure, exécution sur du matériel déjà possédé | Transparence jugée faible par un tiers indépendant (score climat 23/100) ; seule donnée disponible = déclaration non vérifiée du CEO | **La plus transparente du marché** : première analyse de cycle de vie d'un LLM publiée avec l'ADEME et Carbone 4, conforme ISO 14040/44 | Aucune donnée environnementale publiée identifiée |
| Confidentialité | **Totale** : aucune donnée ne quitte la machine | Envoi à un tiers basé aux États-Unis | Envoi à un tiers (hébergement UE possible) | Envoi à un tiers basé aux États-Unis |
| Coût | **0 €** | Facturé à l'usage | Facturé à l'usage | Compétitif mais non nul |

Point méthodologique assumé : les données environnementales citées (Mistral, OpenAI) proviennent de méthodologies différentes et ne sont **pas directement comparables entre elles** en valeur absolue. C'est précisément l'absence d'un référentiel commun qui a été retenue comme argument : la **transparence elle-même** (publiée ou non, vérifiée par un tiers ou déclarative) devient un critère de choix pertinent indépendamment des chiffres exacts.

### 3.3 Conclusion argumentée

| | Répond au besoin ? | Avantages | Inconvénients |
|---|---|---|---|
| **Ollama** | ✅ Oui — solution retenue | Zéro coût, zéro compte, confidentialité totale, déjà installé et fonctionnel | Qualité d'extraction à valider par le POC |
| Mistral API | ⚠️ Partiellement | Le plus transparent sur l'impact environnemental, entreprise européenne | Compte requis, donnée envoyée à un tiers |
| Groq | ⚠️ Partiellement | Débit et rapport qualité/prix excellents | Compte requis, aucune transparence environnementale, coût non nul |
| OpenAI API | ❌ Non retenu | Qualité et documentation de référence | Compte requis, coût, transparence environnementale jugée faible |

Ollama est le seul service qui satisfait *simultanément* les quatre contraintes du projet. Ce constat est explicitement nuancé dans le document source : les trois services cloud répondraient chacun techniquement au besoin fonctionnel, et seraient à reconsidérer si le projet sortait du cadre pédagogique et acceptait un budget et un compte fournisseur — Mistral se distinguant alors nettement sur la transparence environnementale. Cette conclusion nuancée plutôt que binaire («Ollama, point final ») documente une vraie démarche de comparaison, pas une décision prise d'avance et justifiée après coup.

## 4. C8 — POC du service IA retenu

### 4.1 Installation, accès et modèle retenu

Ollama était déjà installé sur le poste de développement (version `0.32.5`, confirmée en S4). Le modèle retenu pour le test de faisabilité, `llama3.2:3b` (Meta, quantification Q4_K_M, ~3,1 Go en mémoire), a été choisi pour son faible encombrement — adapté à un poste sans GPU dédié obligatoire — et sa large adoption dans l'écosystème Ollama.

Point de sécurité documenté plutôt qu'implicite : Ollama n'expose par défaut aucune authentification, mais **n'écoute que sur `localhost`**, ce qui constitue en soi le contrôle d'accès pour un usage en développement. Si le service devait un jour être exposé au-delà du poste local, `OLLAMA_HOST` et un reverse-proxy authentifié seraient nécessaires — noté comme point de vigilance pour un déploiement réel plutôt que traité comme non pertinent.

### 4.2 Interconnexion avec les autres composants

Confirmation de la veille S4 (§2.4) : Ollama expose une API compatible OpenAI (`/v1/chat/completions`), ce qui permet d'utiliser le client Python `openai` standard sans écrire de client HTTP dédié :

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")  # cle ignoree par Ollama, requise par le client
```

Le script de POC (`ai-service/poc/extraction_poc.py`) va chercher ses données de test via l'**API Data du Bloc 1** déjà en service depuis S3, sans lecture de fichier ni accès direct à une base d'un autre composant — cohérence architecturale déjà respectée dès cette étape exploratoire, pas seulement une fois le produit « fini ». Seul le texte d'ingrédients (donnée publique Open Food Facts) est transmis au modèle : aucune donnée personnelle ni de santé n'entre en jeu à ce stade.

### 4.3 Protocole de test de faisabilité

10 produits réels ont été récupérés via l'API Data (`GET /produits` puis `GET /produits/{code_barres}`) et les allergènes extraits par le modèle comparés aux allergènes déjà référencés par Open Food Facts, utilisée comme vérité terrain approximative (Open Food Facts n'est lui-même ni exhaustif ni infaillible, mais reste la meilleure référence disponible à ce stade du projet).

### 4.4 Itération 1 — prompt de base

| Métrique | Résultat |
|---|---|
| Précision | 86 % |
| Rappel | 33 % |

Le modèle détecte correctement le gluten et le lait dans la plupart des cas, mais rate systématiquement les allergènes moins évidents : sur 3 houmous contenant explicitement « Tahini Sesame Seed Paste » / « purée de sésame » / « SESAME SEED PASTE » dans le texte, **aucun n'a été détecté**.

### 4.5 Itération 2 — prompt enrichi de synonymes

Hypothèse testée : le modèle ne relie pas le mot « sésame » présent dans le texte à la catégorie officielle « Graines de sésame ». Le prompt a été enrichi d'une liste de synonymes par allergène.

| Métrique | Résultat |
|---|---|
| Précision | 75 % (en baisse) |
| Rappel | 33 % (inchangé) |

Résultat rapporté honnêtement plutôt que minimisé : l'enrichissement du prompt **n'a pas amélioré le rappel**, et a même introduit un faux positif supplémentaire (gluten hallucinée sur un houmous n'en contenant pas). Le mot « sésame », pourtant présent tel quel dans le texte, n'est toujours pas relié à la catégorie attendue.

### 4.6 Interprétation et recommandation

Le facteur limitant n'est pas la formulation du prompt mais la capacité du modèle 3B lui-même à appliquer une instruction de correspondance sur 14 catégories avec leurs synonymes — limite honnête à documenter plutôt qu'à masquer derrière un prompt toujours plus long.

Le service est **installé, accessible et fonctionnellement intégrable** (C8 satisfait), mais la qualité d'extraction *à elle seule* est jugée insuffisante pour un cas d'usage sécuritaire : un allergène raté a des conséquences réelles pour l'utilisateur. Recommandation retenue pour S6, et effectivement implémentée (voir rapport E3) : ne pas se reposer uniquement sur le modèle, coupler l'extraction IA à une recherche par mots-clés déterministe, et retenir l'**union** des deux détections — un faux positif occasionnel est préférable à un allergène non signalé.

## 5. Grille d'auto-évaluation par compétence

Cette section confronte, pour chaque compétence, ce qui était attendu à ce qui a été réellement produit et vérifié — dans un esprit d'auto-évaluation honnête plutôt que de simple récapitulatif des livrables déjà décrits plus haut.

### C6 — Veille technique et réglementaire

| Aspect attendu | Constat |
|---|---|
| Une thématique de veille définie et justifiée | Deux axes retenus (réglementaire, technique), tous deux directement mobilisés par des décisions de conception ultérieures — pas une veille générique déconnectée du projet |
| Un outillage de collecte adapté | Script reproductible, sans compte, versionné — cohérent avec la contrainte budgétaire plutôt qu'un choix de facilité |
| Une évaluation critique des sources | Chaque source retenue est justifiée sur un critère de fiabilité explicite (auteur identifiable, procédure tracée), et des sources concurrentes ont été examinées puis écartées avec leur raison consignée |
| Une restitution exploitable et accessible | Document Markdown structuré, actions tracées jusqu'à leur mise en œuvre effective (§2.4) |
| **Point de vigilance identifié a posteriori** | La veille reste portée en solo sur un rythme hebdomadaire ; dans un contexte d'équipe, une répartition des sources entre plusieurs veilleurs permettrait une fréquence de vérification plus fine sans alourdir la charge individuelle |

### C7 — Identification et comparaison de services IA

| Aspect attendu | Constat |
|---|---|
| Plusieurs services identifiés, pas un seul évalué par défaut | 4 étudiés en détail, 3 identifiés et explicitement écartés avec raison — 7 services considérés au total |
| Des critères de comparaison explicites et pertinents au besoin | 5 critères (adéquation fonctionnelle, contraintes techniques, éco-responsabilité, confidentialité, coût), chacun directement issu d'une contrainte posée au cadrage, pas une grille générique importée telle quelle |
| Une conclusion argumentée, pas une préférence a priori | La solution la moins chère (Ollama, déjà installée) est aussi celle qui a été objectivement comparée point par point — la convergence entre commodité et choix méthodique est signalée explicitement pour ne pas paraître suspecte |
| **Point de vigilance identifié a posteriori** | La grille de comparaison n'intègre pas de critère de **qualité mesurée** (ce point est volontairement reporté à C8, le POC) — une grille idéale préciserait dès le benchmark qu'un score qualité viendra la compléter, pour éviter de lire la conclusion de C7 comme définitive avant le test réel |

### C8 — Paramétrage et test de faisabilité d'un service IA

| Aspect attendu | Constat |
|---|---|
| Installation et configuration effectivement réalisées, pas seulement documentées en théorie | Version vérifiée (`ollama --version`), modèle réellement téléchargé et chargé, interconnexion testée avec du code réel (pas un extrait de documentation recopié) |
| Un protocole de test explicite et reproductible | 10 produits réels, comparaison à une vérité terrain déclarée avec ses limites (Open Food Facts n'est pas parfait) plutôt que présentée comme absolue |
| Un résultat honnête, y compris s'il est défavorable | Rappel de 33 % rapporté sans enjolivement, y compris la dégradation de précision lors de la seconde itération — un résultat qui aurait pu être caché ou minimisé sans que le jury puisse le vérifier autrement |
| Une recommandation concrète tirée du test | Architecture hybride IA + mots-clés, décision explicite qui engage la conception du bloc suivant, pas une simple note de bas de page |
| **Point de vigilance identifié a posteriori** | Un seul modèle a été testé ; le POC ne permet donc pas de distinguer une limite du modèle `llama3.2:3b` spécifiquement d'une limite plus générale des modèles de cette taille — nuance importante pour ne pas sur-généraliser la conclusion |

## 6. Synthèse transversale

Les trois compétences de ce bloc s'enchaînent logiquement et se sont mutuellement informées : la veille (C6) a directement influencé une décision d'implémentation (client `openai` standard) reprise dans le benchmark puis le POC ; le benchmark (C7) a établi une grille de critères objective avant tout test technique, évitant de choisir Ollama par simple convenance (déjà installé) sans l'avoir comparé méthodiquement ; le POC (C8) a confirmé la faisabilité technique tout en révélant honnêtement une limite fonctionnelle qui a changé la conception du bloc suivant.

Ce dernier point est le résultat le plus significatif de ce cas pratique : un POC qui aurait seulement cherché à confirmer la solution retenue en amont n'aurait pas la même valeur qu'un POC qui teste réellement, documente un résultat mitigé (rappel de 33 %), et en tire une **décision de conception concrète** (architecture hybride IA + mots-clés) plutôt que de conclure « ça marche » sur la base du seul cas favorable.

## 7. Limites assumées et perspectives

- Le test de faisabilité porte sur 10 produits, échantillon volontairement restreint pour un POC dans un projet pédagogique solo — la mesure définitive de qualité (précision/rappel sur un jeu de référence plus large et gelé) est traitée en S7 (C12, golden dataset de 11 cas, voir rapport E3).
- Les données environnementales comparées dans le benchmark (§3.2) reposent sur des méthodologies hétérogènes et ne permettent pas de chiffrer un gain carbone exact du choix Ollama — seule la tendance et la transparence relative des acteurs ont été retenues comme signal exploitable.
- Le POC n'a testé qu'un seul modèle (`llama3.2:3b`) ; l'alternative identifiée en veille (LFM2.5-2.6B) n'a pas été essayée, le modèle initial s'étant révélé suffisant pour poursuivre — un projet visant une qualité d'extraction supérieure gagnerait à comparer plusieurs tailles de modèle sur le même golden dataset.

## 8. Conclusion

Le Bloc 2, dans sa phase d'exploration (C6-C8), a permis de choisir un service d'IA conforme à toutes les contraintes du projet (Ollama), de le paramétrer, et surtout d'en tester la fiabilité réelle avant de construire dessus — révélant une limite fonctionnelle importante qui a directement façonné l'architecture retenue pour la suite du Bloc 2 (S6-S8, voir rapport E3). C'est cette articulation entre veille, comparaison objective et test empirique honnête qui constitue la valeur ajoutée de ce cas pratique, davantage que le choix technique final pris isolément.
