# Monitoring du modèle IA (C11) — S7

## 1. Métriques suivies

| Métrique | Explication | Pourquoi elle est pertinente ici |
|---|---|---|
| **Précision** | Part des allergènes signalés qui sont réellement présents (VP / (VP + FP)) | Un faux positif fréquent use la confiance de l'utilisateur dans l'outil |
| **Rappel** | Part des allergènes réellement présents qui ont été signalés (VP / (VP + FN)) | Un allergène manqué a une conséquence de sécurité réelle — la métrique la plus critique du projet |
| **Faux positifs / faux négatifs (comptes bruts)** | Volume absolu, pas seulement le taux | Permet de savoir si un mauvais score vient de nombreuses petites erreurs ou d'un seul cas problématique |
| **Latence moyenne / médiane / max** | Temps d'une analyse complète (IA + mots-clés) | Le modèle tourne en local : la latence dépend directement des ressources de la machine, à surveiller pour l'expérience utilisateur (voir le correctif de timeout du prototype, [prototype.md](prototype.md)) |

Ces métriques sont calculées sur le [golden dataset](../../ai-service/common/golden_dataset.py) (C12) : le même calcul sert à la fois de porte de qualité automatisée (tests) et de suivi dans le temps (monitoring) — deux usages du même outil de mesure plutôt que deux implémentations séparées.

## 2. Outil retenu et justification

**MLflow**, déjà cité dans la stack technique du référentiel. Choisi parce qu'il coche toutes les contraintes déjà posées pour ce projet :

- Gratuit, **aucun compte** requis, stockage local par fichiers (`ai-service/data/mlflow/`, non versionné — voir `.gitignore`).
- Tableau de bord web natif (`mlflow ui`) sans configuration supplémentaire.
- Conçu pour comparer plusieurs exécutions dans le temps — exactement le besoin ici (mesurer l'effet d'une modification du prompt ou du dictionnaire de synonymes).

## 3. Restitution en temps réel et accessibilité

- **Tableau de bord MLflow** (`mlflow ui`, `http://localhost:5000`) : vecteur de restitution principal, consulté et vérifié fonctionnel en conditions réelles (voir section 5).
- **Rapport JSON complémentaire** (`ai-service/data/raw/monitoring/dernier_rapport_evaluation.json`, journalisé comme artefact MLflow) : MLflow étant un outil tiers dont la conformité WCAG n'a pas été auditée par nos soins, ce rapport structuré sert de restitution alternative, exploitable par un lecteur d'écran ou tout autre outil, pour les parties prenantes qui ne pourraient pas utiliser l'interface web de MLflow dans de bonnes conditions.
- Ce document lui-même (structure par titres, tableaux à en-têtes explicites) constitue une troisième restitution, textuelle et versionnée.

## 4. Test en bac à sable avant utilisation réelle

Avant d'être considérée opérationnelle, la chaîne a été testée en environnement de développement local (pas de serveur MLflow distant, pas de partage d'accès) : voir section 5, une exécution complète et une vérification du tableau de bord ont précédé toute utilisation « en production » (S8, intégration dans la CI/CD MLOps).

## 5. Constat d'exécution réel

```bash
cd ai-service
py -m monitoring.evaluer_modele
py -m mlflow ui --backend-store-uri file:///.../ai-service/data/mlflow --port 5000
```

Résultat de la première exécution (expérience `nutriscan-extraction-allergenes`, run `funny-fox-899`) :

| Métrique | Valeur |
|---|---|
| Précision | 67 % |
| Rappel | 100 % |
| Vrais positifs / Faux positifs / Faux négatifs | 12 / 6 / 0 |
| Latence moyenne | 17,8 s |

**Découverte faite grâce à ce monitoring** : le modèle `llama3.2:3b` affiche un **biais systématique de sur-détection du gluten** — 5 des 6 faux positifs de cette exécution sont « Gluten (cereales) », y compris sur un jus de fruits sans aucun rapport (« 70% jus d'orange, 30% purée de fraise »). Le filet de sécurité par mots-clés, lui, atteint 100 % de précision et de rappel sur le même jeu de données : sur ce golden dataset, l'IA n'apporte donc actuellement aucun bénéfice de rappel et dégrade la précision globale. C'est exactement le type d'amélioration itérative que ce monitoring doit permettre de détecter (voir critère C11) :

**Recommandations pour la suite** (à arbitrer en fonction du temps disponible, hors périmètre de S7) :
1. Essayer un autre modèle (Mistral 7B, ou un modèle plus récent) pour voir si ce biais est spécifique à `llama3.2:3b`.
2. Affiner le prompt pour réduire spécifiquement les faux positifs sur le gluten (ex. exiger la présence explicite d'un nom de céréale).
3. À défaut d'amélioration, envisager de retirer l'IA du calcul de `allergenes_detectes` pour ce projet et de ne conserver que le filet de mots-clés comme mécanisme principal — décision à documenter explicitement si elle est prise, car elle change l'architecture actée en S5-S6.

## 6. Installation et utilisation

```bash
cd ai-service
py -m pip install -r requirements.txt
ollama serve                       # si pas deja demarre
py -m monitoring.evaluer_modele    # lance une evaluation et journalise dans MLflow
py -m mlflow ui --backend-store-uri "$(py -c "from common.io_utils import get_data_dir; print(get_data_dir('mlflow').as_uri())")" --port 5000
```

Le tableau de bord est alors accessible sur `http://localhost:5000`. Chaque nouvelle exécution de `evaluer_modele.py` crée un nouveau run comparable aux precedents dans la meme experience.
