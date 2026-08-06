# Anticipation des questions du jury (S13)

Questions probables par thème, avec une réponse préparée courte (à dire en 30 s à 1 min à l'oral, pas à lire). Chaque réponse s'appuie sur un fait réel du projet, jamais une justification inventée sur le moment.

## Questions transverses (architecture, méthodologie)

**« Pourquoi ce refus systématique de créer un compte, même pour des outils internes comme la veille ou le monitoring ? »**
Contrainte posée dès le cadrage (S1), directement héritée du choix du sujet lui-même (un sujet initial a été abandonné pour cette raison). Elle garantit la reproductibilité du projet par un tiers sans démarche administrative, et renforce l'argument de confidentialité pour la donnée de santé (allergies) : moins de tiers dans la chaîne, moins de surface d'exposition.

**« Si vous deviez recommencer, que feriez-vous différemment ? »**
Ne pas répondre « rien » — donner un exemple concret et assumé : relire le cahier des charges juste avant chaque nouveau développement de fonctionnalité, pas seulement au cadrage initial (le score nutritionnel, prévu dès S1, n'a été réellement implémentable qu'après un retour en arrière sur le Bloc 1 en S9).

**« Ce projet a-t-il été testé en charge / avec plusieurs utilisateurs simultanés ? »**
Non, explicitement hors périmètre d'un projet pédagogique solo sur 13 semaines. Deux limites connues et documentées le confirment : la limitation de débit de l'API IA et le compteur anti-bruteforce de l'application sont tous deux en mémoire, mono-instance — un déploiement à plusieurs instances nécessiterait un compteur partagé (Redis).

**« Pourquoi Streamlit et pas un framework front plus classique (React, Vue) ? »**
Cohérence avec l'objectif du projet (démontrer les compétences IA/data du référentiel, pas un exercice de front-end) et rapidité de mise en œuvre pour un développeur solo sur 13 semaines. Le compromis assumé : moins de contrôle fin sur certains comportements (voir le bug du widget conditionnel dans un `st.form`, trouvé et corrigé en S9).

## Questions Bloc 1 (données, RGPD)

**« Le corpus de recettes ne fait que 10 entrées, n'est-ce pas trop peu pour être représentatif ? »**
Oui, volontairement restreint pour un projet pédagogique — mais le code (pagination, gestion des erreurs 429/5xx, retries) est écrit pour un volume plus grand sans modification. La preuve : le rapprochement Ciqual, testé sur ce même corpus, obtient 80 % de couverture réelle, un signal de robustesse indépendant de la taille de l'échantillon.

**« Comment garantissez-vous que le profil allergène ne peut pas fuiter en cas de compromission de la base ? »**
Chiffrement au repos avec `pgcrypto` sur la colonne `niveau_chiffre`, clé applicative fournie par variable d'environnement, jamais stockée en base. Une compromission de la seule base ne suffirait donc pas à lire le profil en clair.

**« Pourquoi ne pas avoir répliqué tout l'export Open Food Facts dans votre base ? »**
Volumétrie (plusieurs millions de lignes) disproportionnée pour l'usage réel de l'application ; l'export est interrogé ponctuellement via DuckDB pour la seule compétence « système big data », pas répliqué en continu — choix aussi cohérent avec l'objectif de sobriété numérique posé au cadrage.

## Questions Bloc 2 (IA)

**« Pourquoi ne pas avoir choisi un modèle plus gros/plus récent qui aurait peut-être mieux détecté les allergènes ? »**
Le POC a testé un seul modèle (`llama3.2:3b`), adapté à un poste de développement standard sans GPU dédié. Le facteur limitant identifié (rappel de 33 %) n'a pas été isolé comme spécifique à ce modèle précis — un projet visant une meilleure qualité d'extraction comparerait plusieurs tailles de modèle sur le même golden dataset, explicitement noté comme perspective non réalisée ici.

**« Si l'IA ne fonctionne pas bien, pourquoi la garder dans l'architecture ? »**
Parce que le filet de mots-clés seul est déterministe mais rigide (ne couvre que les synonymes explicitement listés), alors que l'IA capture parfois des formulations non anticipées. Le monitoring a montré qu'aujourd'hui, sur le golden dataset, l'IA n'apporte pas de gain de rappel net et dégrade la précision (biais de sur-détection du gluten) — un résultat honnêtement rapporté, avec une recommandation explicite d'arbitrage (changer de modèle, affiner le prompt, ou retirer l'IA du calcul) volontairement laissée ouverte plutôt que tranchée sans données suffisantes.

**« Votre CI/CD MLOps entraîne-t-elle le modèle ? »**
Non, et c'est volontairement précisé dans la documentation : le modèle est pré-entraîné et utilisé tel quel (Ollama). La chaîne couvre test des données, évaluation/validation du modèle, et packaging — le vocabulaire du référentiel est respecté littéralement plutôt que réinterprété.

**« Comment mesurez-vous objectivement que le modèle est "assez bon" ? »**
Des seuils plancher mesurés, pas espérés a priori : précision ≥ 60 %, rappel ≥ 95 %, calibrés à partir d'une exécution réelle du monitoring documentée dans le rapport E3, pas fixés arbitrairement avant d'avoir vu un résultat.

## Questions Bloc 3 (application, sécurité, incidents)

**« Votre application est-elle réellement accessible aujourd'hui, avec une URL publique ? »**
Non — décision assumée et documentée : le déploiement continu publie des images Docker versionnées sur GitHub Container Registry, prêtes à déployer, mais sans mise en ligne effective chez un hébergeur tiers, pour ne pas contredire le principe zéro-compte externe posé dès le cadrage. C'est un choix de cohérence architecturale, pas un renoncement technique — le `docker pull` + `docker run` fonctionne sur n'importe quel hôte Docker.

**« Quel est, selon vous, le bug le plus grave que vous avez trouvé sur ce projet ? »**
Deux candidats sérieux, tous deux liés à la sécurité des données de santé : (1) un profil allergène qui aurait pu être silencieusement écrasé par une liste vide en cas de panne du backend pendant le chargement initial ; (2) une panne d'Ollama qui faisait échouer *toute* l'analyse, y compris le filet de mots-clés qui ne nécessite aucun réseau — annulant la garantie même de l'architecture hybride. Les deux ont été trouvés en provoquant réellement une panne, pas en relisant le code.

**« Comment avez-vous vérifié que votre application respecte l'accessibilité WCAG ? »**
Vérification dans le navigateur à chaque étape, pas seulement une relecture du code : arbre d'accessibilité inspecté pour confirmer les labels de formulaire, cases à cocher individuellement étiquetées, jamais de statut de compatibilité porté par la seule couleur (icône + texte systématiques). Limite assumée : pas d'audit avec un outil automatisé dédié (axe, Lighthouse) ni de test avec un vrai lecteur d'écran — vérification manuelle documentée comme telle.

**« Que se passe-t-il si PostgreSQL tombe en panne ? »**
Non testé empiriquement dans ce projet (limite assumée, voir rapport E5) — seules les pannes de l'API Data et d'Ollama ont été réellement provoquées. Le comportement attendu (erreurs 500 génériques côté API, propagées comme les autres pannes de service) suit la même logique de gestion d'erreur déjà vérifiée ailleurs, mais sans preuve empirique directe.

## Questions « pièges » à préparer sans filet

**« Est-ce que tout ce que vous avez montré aujourd'hui fonctionne vraiment, ou est-ce préparé/simulé ? »**
Réponse à ancrer sur du concret : citer un ou deux exemples précis de bugs trouvés en testant réellement (ex. le faux négatif multilingue en S6, le biais gluten en S7, la panne Ollama en S11) — la meilleure preuve que le projet a été vérifié en conditions réelles, pas seulement conçu puis présenté comme fonctionnant.

**« Vous avez travaillé seul — comment avez-vous géré la coordination/l'agilité (C16) sans équipe ? »**
Rituels explicites même en solo : revue hebdomadaire de la matrice de compétences, mise à jour du board en fin de semaine, traçabilité systématique tâche → commit → compétence. Limite assumée : jamais mis à l'épreuve d'une vraie négociation de priorités entre plusieurs personnes — limite structurelle du format solo.

**« Combien de temps avez-vous vraiment passé sur ce projet, et où sont les raccourcis ? »**
Répondre avec honnêteté sur les limites déjà documentées plutôt que prétendre l'absence de compromis : échantillons de données volontairement restreints (Bloc 1), couverture multilingue partielle (FR/EN/DE), pas de déploiement pré-production réel (Bloc 3) — chacun documenté avec sa raison, pas découvert par le jury en creusant.
