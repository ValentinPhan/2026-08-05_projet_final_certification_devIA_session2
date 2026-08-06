# Support de présentation — NutriScan IA (S13)

Plan de diapositives, organisé en **modules indépendants** parce que chaque épreuve (E1-E5) a son propre format d'oral :

| Épreuve | Durée orale | Module à utiliser |
|---|---|---|
| E1 | 15 min + 10 min questions | Module 0 (intro courte) + Module E1 |
| E2 | 15 min + 10 min questions | Module 0 (intro courte) + Module E2 |
| E3 | 20 min + démo | Module 0 + Module E3 + démo (voir `script-demo.md`) |
| E4 | 20 min + démo | Module 0 + Module E4 + démo |
| E5 | 10 min + 10 min questions | Module 0 (très court) + Module E5 |

Si une seule soutenance couvre l'ensemble du projet, enchaîner Module 0 → E1 → E2 → E3 (+ démo) → E4 (+ démo) → E5 → Conclusion générale, en resserrant chaque module au strict nécessaire pour tenir dans le temps global imparti par le jury.

Convention : chaque diapositive est un titre + des puces courtes (jamais de paragraphe à lire à l'écran) ; les points en *italique* sont des notes pour l'oral, à dire mais pas à afficher.

---

## Module 0 — Introduction commune (2-3 min)

### Diapo 1 — Titre
- **NutriScan IA** — assistant de compatibilité alimentaire
- Certification Développeur en Intelligence Artificielle — RNCP, Simplon Lyon
- [Nom du candidat], session 2026

### Diapo 2 — Le problème
- Un consommateur allergique/intolérant doit lire manuellement chaque étiquette
- Exercice fastidieux, source d'erreur — en particulier sur des recettes qui ne mentionnent pas explicitement l'allergène
- *Exemple concret à donner à l'oral : une pizza aux ingrédients en allemand, un allergène caché dans une sous-recette*

### Diapo 3 — La réponse
- Profil alimentaire déclaré → recherche produit/recette → analyse de compatibilité par IA → score nutritionnel + historique
- ⚠️ Aide à la lecture d'étiquettes, **pas un avis médical**

### Diapo 4 — Une contrainte fondatrice, pas un détail
- **Zéro compte, zéro clé API** sur toute la chaîne
- *Pourquoi le dire tôt : cette contrainte a orienté quasiment chaque choix technique du projet (données ouvertes, IA locale, CI/CD sans hébergeur tiers) — elle doit être présentée comme un choix de conception assumé, pas une contrainte subie*

### Diapo 5 — Architecture en 3 blocs
- Diagramme : `data-pipeline` (données) → `ai-service` (IA) → `app` (application)
- Communication strictement par API REST, jamais d'accès direct à la base d'un autre composant
- *Insister : ce découpage correspond exactement au découpage des épreuves — pas un hasard, une décision de S1*

---

## Module E1 — Bloc 1, données (C1-C5)

### Diapo E1.1 — Les 4 sources (C1)
- API REST (Open Food Facts), scraping (Wikibooks, licence libre), fichier (Ciqual/ANSES), big data (export OFF via DuckDB)
- Chiffres réels : 47 fiches produits, 10 recettes, 3186 aliments Ciqual

### Diapo E1.2 — Une requête analytique et ses optimisations (C2)
- Répartition des Nutri-Score des produits vendus en France, sur 500 000 lignes d'un export de 4,65 M
- *Point fort à mentionner : le choix CSV plutôt que Parquet distant vient d'une mesure réelle (Parquet impraticable en pratique), pas d'une préférence a priori*

### Diapo E1.3 — Nettoyage et traçabilité (C3)
- Règles de nettoyage propres à chaque source, motifs d'exclusion journalisés (pas masqués)
- Exemple : 21/47 produits écartés (texte d'ingrédients absent) — compté et expliqué, pas caché

### Diapo E1.4 — Une base conforme RGPD dès la conception (C4)
- Modèle Merise → PostgreSQL, chiffrement `pgcrypto` de la donnée de santé (profil allergène)
- Registre des traitements, droits des personnes (accès/effacement/portabilité)

### Diapo E1.5 — API Data (C5)
- FastAPI, JWT, documentation OpenAPI automatique
- Périmètre de sécurité volontaire : **aucune donnée personnelle** n'y transite

### Diapo E1.6 — Ce qui a été appris
- `robots.txt` faussement bloquant, incompatibilité Python 3.9/Pydantic, port en conflit
- *Message clé : chaque problème a été trouvé en exécutant le code, pas en le relisant*

---

## Module E2 — Bloc 2, veille/benchmark/POC (C6-C8)

### Diapo E2.1 — Pourquoi une IA ici
- Extraire les allergènes d'un texte libre, multilingue, non structuré

### Diapo E2.2 — Veille : deux axes, quatre sources fiables (C6)
- Réglementaire (CNIL, EFSA) / technique (Ollama, Hugging Face)
- *Exemple d'action concrète tirée de la veille : le format de streaming Ollama aligné sur OpenAI → décision d'utiliser le client `openai` standard*

### Diapo E2.3 — Benchmark : Ollama vs 3 concurrents cloud (C7)
- Grille : adéquation fonctionnelle, contraintes techniques, éco-responsabilité, confidentialité, coût
- Ollama seul à satisfaire *simultanément* toutes les contraintes du projet
- *Nuance à garder : les concurrents cloud répondraient techniquement au besoin — la conclusion n'est pas binaire*

### Diapo E2.4 — Le POC révèle une vraie limite (C8)
- Itération 1 : précision 86 %, **rappel 33 %**
- Itération 2 (prompt enrichi) : rappel toujours à 33 %
- *Message clé, à ne pas édulcorer : le problème n'était pas le prompt mais la capacité du modèle 3B — dit clairement à l'oral, c'est ce qui montre la rigueur de la démarche*

### Diapo E2.5 — La décision qui en découle
- Ne jamais reposer uniquement sur l'IA → **architecture hybride IA + mots-clés**, union des deux détections
- Cette décision structure tout le reste du Bloc 2 (E3)

---

## Module E3 — Bloc 2, API IA/monitoring/CI-CD (C9-C13) — 20 min + démo

### Diapo E3.1 — L'API IA (C9)
- Orchestre modèle local + API Data, calcul de compatibilité toujours déterministe
- Sécurité OWASP : limitation de débit, aucune donnée personnelle envoyée au modèle

### Diapo E3.2 — Intégration prototype (C10)
- Streamlit consommant l'API IA + l'API Data, rien de plus
- **Deux bugs réels trouvés en testant manuellement** : timeout trop court, faux négatif multilingue (lait non détecté sur un produit allemand)
- *Le faux négatif est l'exemple le plus fort du rapport — à raconter avec le détail réel (produit, allergène, conséquence)*

### Diapo E3.3 — Monitoring : un biais découvert, pas supposé (C11)
- MLflow, précision/rappel/latence sur le golden dataset
- **Sur-détection du gluten par le modèle** : 5 des 6 faux positifs, y compris sur un jus de fruits
- Le filet de mots-clés seul fait 100 %/100 % sur ce jeu — l'IA n'apporte alors aucun bénéfice net

### Diapo E3.4 — Tests à 3 niveaux (C12)
- Données → mots-clés (11 cas) → pipeline complet (seuils mesurés : précision ≥60 %, rappel ≥95 %)
- Limite assumée : le cas de la sous-recette (quiche lorraine), documentée plutôt que masquée par une règle fragile

### Diapo E3.5 — CI/CD MLOps (C13)
- 3 jobs GitHub Actions : tests données → évaluation (vrai Ollama) → packaging GHCR
- **2 bugs réels trouvés uniquement en conditions réelles** : `MLFLOW_ALLOW_FILE_STORE`, nom d'image GHCR en minuscules
- Run final : succès en 7 min 45 s

### → Transition démo
- *« Je vais maintenant montrer l'application en fonctionnement réel, y compris un cas où l'IA se trompe et où le filet de mots-clés rattrape l'erreur »* — voir `script-demo.md`

---

## Module E4 — Bloc 3, cadrage/application/CI-CD (C14-C19) — 20 min + démo

### Diapo E4.1 — Le cadrage, référence active sur 10 semaines (C14-C16)
- Cahier des charges, user stories (9), Merise, architecture — posés en S1
- *Preuve de robustesse à donner : la contrainte zéro-compte posée en S1 a explicitement tranché un choix d'hébergement en S10, 9 semaines plus tard*

### Diapo E4.2 — L'application (C17)
- Backend FastAPI (comptes, profil chiffré, historique, RGPD) + frontend Streamlit
- Refonte assumée : l'architecture initiale prévoyait un seul bloc « front+back », scindé en S9 pour rester cohérent avec le reste du système
- **Bug le plus grave du rapport** : un profil vide mis en cache pendant une panne aurait pu écraser silencieusement le vrai profil — corrigé avant toute mise en service

### Diapo E4.3 — Sécurité et accessibilité vérifiées, pas déclarées
- bcrypt, anti-énumération de comptes, anti-bruteforce, jetons de session dédiés
- Accessibilité testée dans le navigateur : cases à cocher individuelles, jamais de statut porté par la seule couleur

### Diapo E4.4 — CI applicative (C18)
- Lint + tests contre un vrai conteneur PostgreSQL (pas des mocks)
- Bug réel trouvé au premier run : version de Starlette exigeant un nouveau paquet (`httpx2`)

### Diapo E4.5 — CD applicative (C19)
- Publication d'images Docker sur GitHub Container Registry, déclenchée uniquement après succès de la CI
- **Décision assumée** : pas de déploiement chez un hébergeur tiers (aurait exigé un compte, contraire au principe posé en S1)
- Gating vérifié en conditions réelles : un run correctement `skipped`, un run réussi

### → Transition démo
- *Montrer le parcours complet : inscription → profil → recherche produit → alerte → historique → export RGPD*

---

## Module E5 — Bloc 3, monitoring app/incidents (C20-C21) — 10 min

### Diapo E5.1 — Surveillance de l'application (C20)
- Logs structurés JSON (jamais de donnée de santé en clair), métriques Prometheus, tableau de bord Grafana
- Bug réel : image Grafana `latest` cassée, épinglée à une version stable

### Diapo E5.2 — Deux pannes réellement provoquées (C21)
- Panne API Data → 4 bugs frontend, dont un risque de perte du profil allergène
- **Panne Ollama → le bug le plus critique du projet** : l'analyse échouait totalement au lieu de dégrader sur le filet de mots-clés
- *Phrase clé à préparer : « cette panne annulait la garantie même pour laquelle l'architecture hybride avait été conçue »*

### Diapo E5.3 — Résolution et clôture d'US9
- Mode dégradé explicite (`ia_disponible: false`), jamais un échec silencieux
- Correctif inter-blocs assumé : le code du Bloc 2 a été modifié depuis un exercice du Bloc 3 — un incident réel ne respecte pas les frontières de compétences

---

## Conclusion générale (si soutenance unique)

### Diapo finale — Bilan
- 21/21 compétences couvertes, chaque bloc vérifié en conditions réelles (pas seulement conçu)
- Une dizaine de bugs réels trouvés et corrigés, documentés plutôt que masqués — c'est la méthode, pas un aveu de faiblesse
- Limite assumée la plus importante à citer si demandé : le déploiement pré-production s'arrête à la publication d'images Docker (choix documenté, pas un oubli)

### Diapo finale — Merci
- Questions du jury
