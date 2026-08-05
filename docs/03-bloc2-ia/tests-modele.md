# Tests automatisés du modèle IA (C12) — S7

## 1. Stratégie de test

Trois niveaux, du plus rapide/déterministe au plus proche des conditions réelles :

| Niveau | Fichier | Portée | Vitesse | Appel réseau |
|---|---|---|---|---|
| 1. Validation des données | `test_modele_qualite.py::test_golden_dataset_structure_valide` | Le [golden dataset](../../ai-service/common/golden_dataset.py) lui-même (cohérence des libellés, non-vide, unicité) | < 1 s | Non |
| 2. Non-régression déterministe | `test_modele_qualite.py::test_detection_mots_cles_sur_jeu_de_reference` (paramétré, 11 cas) | Le filet de sécurité par mots-clés (`detecter_par_mots_cles`) | ~6 s | Non |
| 3. Évaluation du pipeline complet | `test_modele_qualite.py::test_evaluation_hybride_seuils_minimums` | IA + mots-clés ensemble, sur le vrai modèle Ollama | ~3 min | Oui (Ollama local) |

Ce découpage répond à un besoin concret : le niveau 2 aurait, à lui seul, détecté **immédiatement** tous les bugs trouvés manuellement en S6-S7 (terme allemand trop court, mots anglais manquants, synonymes trop génériques comme « farine » ou « beurre », ligature « œ » non normalisée) sans attendre un test manuel dans un navigateur. C'est la justification principale de son existence : remplacer une découverte accidentelle par une détection systématique.

## 2. Outils

**pytest**, déjà utilisé pour l'API Data et l'API IA (cohérence de l'environnement technique du projet) — `pytest.mark.parametrize` pour dérouler le golden dataset cas par cas (échec ciblé et lisible), `pytest.mark.skipif` pour ne pas faire échouer le niveau 3 si Ollama n'est pas démarré.

## 3. Couverture

- **11 cas** dans le golden dataset (produits et recettes réels), couvrant : multi-allergènes simultanés, cas « piège » (produit affiché « gluten free » contenant d'autres allergènes), cas négatifs propres (dont un texte quadrilingue), un cas de précision (lécithine de *tournesol*, pas de soja), et le cas multilingue ayant révélé le bug du prototype S6.
- Les 11 cas passent au niveau 2 (mots-clés seuls, 100 % précision/rappel sur ce jeu).
- Le niveau 3 (pipeline complet) est vérifié au-dessus de seuils plancher **mesurés, pas espérés** : précision ≥ 60 %, rappel ≥ 95 % — voir la justification détaillée et la découverte d'un biais du modèle dans [monitoring-modele.md](monitoring-modele.md).

## 4. Exécution

```bash
cd ai-service
py -m pip install -r requirements.txt

# Niveaux 1 et 2 (rapides, sans Ollama) :
py -m pytest api_ia/tests/test_modele_qualite.py -k "not hybride" -v

# Niveau 3 (necessite Ollama demarre) :
ollama serve
py -m pytest api_ia/tests/test_modele_qualite.py::test_evaluation_hybride_seuils_minimums -v
```

Constat d'exécution :

```
12 passed in 6.22s          # niveaux 1 et 2
1 passed in 190.69s          # niveau 3 (apres calibration des seuils, voir monitoring-modele.md)
```

## 5. Limite assumée : le cas de la recette avec sous-recette

Le cas `recette_quiche_lorraine` illustre une limite architecturale plutôt qu'un bug : l'ingrédient « pâte brisée (recette) » renvoie vers une sous-recette dont le contenu (farine, donc gluten) n'est pas déployé dans le texte analysé. Le gluten réellement présent dans une quiche lorraine n'est donc pas extractible de cette liste d'ingrédients seule. Plutôt que de masquer cette limite en ajoutant une règle ad hoc (ex. reconnaître « pâte brisée » comme synonyme de gluten, ce qui mélangerait un nom de recette avec un ingrédient), elle est documentée explicitement dans le golden dataset et exclue des attendus de ce cas — une limite connue et assumée vaut mieux qu'un correctif fragile.

## 6. Accessibilité

Ce document suit la même structure accessible que les autres livrables du projet (titres hiérarchiques, tableaux à en-têtes explicites, pas d'information portée par la seule mise en forme). La sortie de `pytest` elle-même est un flux texte brut, nativement compatible avec tout lecteur d'écran ou terminal accessible.
