# Script de démonstration live — NutriScan IA (S13)

Deux démonstrations distinctes, l'une pour E3 (service IA, focus résilience), l'autre pour E4 (application complète). Chacune tient en 5-8 minutes pour laisser du temps aux questions.

## 0. Checklist avant la soutenance (à faire *avant* que le jury n'entre, pas en direct)

- [ ] `docker compose up -d postgres api_data api_ia app_backend` — attendre que les 4 conteneurs soient `Up`/`healthy` (`docker compose ps`)
- [ ] `ollama serve` (si pas déjà en service) puis `ollama list` → vérifier que `llama3.2:3b` apparaît
- [ ] **Faire chauffer le modèle** : lancer une analyse de test quelconque (`curl` ou via l'app) *avant* l'arrivée du jury. Ollama décharge le modèle de la mémoire après quelques minutes d'inactivité ; le premier appel après un rechargement à froid peut prendre jusqu'à une minute — un silence d'une minute devant le jury est évitable avec ce simple échauffement.
- [ ] `cd app && py -m streamlit run frontend/main.py`, vérifier que la page se charge sur `http://localhost:8501`
- [ ] Avoir un compte de test déjà créé, avec un profil allergène déjà enregistré (« Lait » en intolérance par exemple) — évite de perdre du temps sur le formulaire d'inscription pendant la démo, sauf si le jury demande spécifiquement à le voir
- [ ] Réduire le zoom du navigateur/terminal pour que le texte soit lisible depuis le fond de la salle
- [ ] Avoir un second onglet ouvert sur un terminal, prêt à taper la commande d'arrêt d'Ollama (voir §2, étape clé)

## 1. Démo E3 — Service IA et résilience (≈ 6 min)

**Objectif** : montrer que l'IA fonctionne réellement, ET que le système reste sûr quand elle tombe en panne — c'est le point le plus fort du projet, à mettre en valeur.

| # | Action | Ce qu'on montre / dit |
|---|---|---|
| 1 | Onglet navigateur sur l'app, page « Rechercher un produit » | *« Voici un produit réel importé depuis Open Food Facts, avec des ingrédients en allemand »* |
| 2 | Sélectionner le produit, cliquer « Analyser ce produit » | Attendre le résultat (quelques secondes, modèle déjà chaud) : statut affiché avec icône + texte, section repliable « Détail de la détection » ouverte pour montrer IA vs mots-clés côte à côte |
| 3 | Ouvrir le détail | *« On voit ici les deux sources de détection — c'est une architecture volontairement hybride, pas seulement l'IA »* |
| 4 | Basculer sur le terminal, taper la commande d'arrêt d'Ollama (`Stop-Process` ou équivalent selon l'OS de démo) | *« Je coupe maintenant volontairement le service IA pour montrer ce qui se passe en cas de panne réelle »* |
| 5 | Revenir sur l'app, relancer une analyse sur un texte contenant un allergène évident (onglet « Texte libre », ex. « lait, sucre, farine ») | Le résultat s'affiche quand même (`⚠️ Service IA temporairement indisponible`), l'allergène est détecté par le filet de mots-clés |
| 6 | Commenter | *« Avant le correctif trouvé en semaine 11, ce même scénario renvoyait une erreur 500 et aucun résultat — y compris pour l'allergène évident. C'est le bug le plus critique de tout le projet, corrigé et maintenant couvert par un test automatisé. »* |
| 7 | Redémarrer Ollama (`ollama serve` en arrière-plan) | *« Le service reprend normalement dès qu'Ollama est de nouveau disponible »* (pas besoin d'attendre le rechargement complet devant le jury si le temps presse — l'essentiel du message est déjà passé) |

**Filet de sécurité si l'étape 5 est plus lente que prévu** : annoncer explicitement *« l'inférence peut prendre jusqu'à une minute après un rechargement à froid, c'est documenté »* plutôt que de rester silencieux — transforme un temps mort en preuve de maîtrise du sujet.

## 2. Démo E4 — Parcours applicatif complet (≈ 7 min)

**Objectif** : montrer que l'application est un produit utilisable de bout en bout, pas une somme de scripts.

| # | Action | Ce qu'on montre / dit |
|---|---|---|
| 1 | Page de connexion | Se connecter avec le compte de test préparé |
| 2 | Page « Mon profil » | Profil déjà rempli (persistant depuis la session précédente) — *« Ce profil est chiffré en base avec pgcrypto, jamais en clair »* |
| 3 | Cocher un nouvel allergène en direct, choisir un niveau, enregistrer | Montre l'interaction réelle (case à cocher individuelle, sélecteur de niveau qui apparaît dynamiquement) |
| 4 | Page « Rechercher une recette » | Choisir une recette, lancer l'analyse, montrer le score nutritionnel agrégé (Ciqual) sous le résultat |
| 5 | Page « Historique » | Montrer que les deux analyses réalisées pendant la démo apparaissent, avec date et statut |
| 6 | Page « Mes données (RGPD) » | Cliquer « Préparer mon export », télécharger le JSON — *« Droit à la portabilité, exécutable en un clic, pas seulement décrit dans un registre »* |
| 7 (optionnel, si le temps le permet) | Montrer l'écran de suppression de compte SANS le confirmer | Souligner la double validation (case à cocher + ressaisie de l'email) — *« Action irréversible, jamais accessible en un seul clic »* |

**Si le jury demande à voir l'inscription** : revenir à l'onglet « Créer un compte », montrer les deux cases de consentement RGPD non pré-cochées et le mot de passe robuste exigé — bon complément si le temps le permet, à ne déclencher que sur demande pour ne pas dépasser le temps imparti.

## 3. Ce qu'il ne faut jamais faire en démo

- Ne jamais promettre un temps de réponse précis pour l'IA (« ça va prendre 3 secondes ») — dire « quelques secondes à une minute selon l'état du modèle » évite toute surprise gênante.
- Ne jamais improviser un scénario non testé à l'avance : chaque étape de ce script a été exécutée réellement pendant le développement (voir les rapports E3/E4/E5) — s'en tenir au script minimise le risque d'un cas limite inattendu devant le jury.
- Si une erreur inattendue survient malgré tout : la commenter ouvertement plutôt que de paniquer (*« voilà un exemple concret de ce que le monitoring du bloc 3 est censé détecter »*) — cohérent avec la méthodologie du projet, qui documente les échecs réels plutôt que de les cacher.
