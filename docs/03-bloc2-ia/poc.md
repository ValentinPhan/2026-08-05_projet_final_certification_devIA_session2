# POC — service IA local (C8) — S5

## 1. Service retenu

**Ollama**, exécuté en local, conformément au [benchmark](benchmark-services-ia.md) : seul service satisfaisant simultanément budget nul, absence de compte et confidentialité totale.

## 2. Installation et accès

| Étape | Commande / constat |
|---|---|
| Installation | Déjà présente sur le poste de développement (confirmé en S4) |
| Version | `ollama --version` → `0.32.5` |
| Démarrage du service | `ollama serve` (expose `http://localhost:11434`) |
| Récupération du modèle | `ollama pull llama3.2:3b` (~2 Go, opération unique) |
| Accès | Aucune authentification par défaut : le service n'écoute que sur `localhost`, ce qui **constitue en soi le contrôle d'accès** (aucune exposition réseau externe). Si le service devait un jour être exposé au-delà du poste local, `OLLAMA_HOST` et un reverse-proxy authentifié seraient nécessaires — noté ici comme point de vigilance pour un déploiement réel. |

## 3. Modèle retenu pour le test de faisabilité

`llama3.2:3b` (Meta, licence Llama 3.2, quantification Q4_K_M, ~3,1 Go en mémoire une fois chargé, fenêtre de contexte 131072 tokens). Choisi comme premier candidat pour son faible encombrement (adapté à un poste de développement standard, sans GPU dédié obligatoire) et sa large adoption dans l'écosystème Ollama.

## 4. Interconnexion avec les autres composants

Ollama expose une **API compatible OpenAI** (`/v1/chat/completions`), point confirmé lors de la veille S4. Le POC s'y connecte avec le client Python `openai` standard, ce qui évite d'écrire un client HTTP dédié et prépare directement l'intégration dans l'API IA du Bloc 2 (S6) :

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")  # cle ignoree par Ollama, requise par le client
```

Le POC (`ai-service/poc/extraction_poc.py`) va chercher ses données de test **via l'API Data du Bloc 1** (`ai-service/common/data_api_client.py`), déjà en service depuis S3 — pas de lecture de fichier ni d'accès direct à une base d'un autre composant, conformément à l'architecture (voir [architecture.md](../01-cadrage/architecture.md)).

## 5. Données impliquées

Le POC transmet au modèle **uniquement le texte d'ingrédients d'un produit** (donnée publique Open Food Facts) — aucune donnée personnelle ni de santé n'est envoyée au modèle à ce stade, cohérent avec le périmètre retenu pour l'API Data (voir [api-data.md](api-data.md)).

## 6. Test de faisabilité

**Protocole** : 10 produits réels (récupérés via `GET /produits` puis `GET /produits/{code_barres}`), comparaison des allergènes extraits par le modèle aux allergènes déjà référencés par Open Food Facts (vérité terrain approximative — Open Food Facts n'est lui-même ni exhaustif ni infaillible, mais reste la meilleure référence disponible à ce stade).

### Itération 1 — prompt de base

| Métrique | Résultat |
|---|---|
| Précision | 86 % |
| Rappel | 33 % |

Le modèle détecte correctement le gluten et le lait dans la plupart des cas, mais **rate systématiquement les allergènes moins évidents** : sur 3 houmous contenant explicitement « Tahini Sesame Seed Paste » / « purée de sésame » / « SESAME SEED PASTE » dans le texte, aucun n'a été détecté.

### Itération 2 — prompt enrichi de synonymes par allergène

Hypothèse testée : le modèle ne relie pas le mot « sésame » présent dans le texte à la catégorie officielle « Graines de sésame ». Le prompt a été enrichi d'une liste de synonymes/formes usuelles par allergène (ex. `Graines de sesame : sesame, tahini, purée/pâte de sésame...`, voir `SYNONYMES_ALLERGENES` dans le script).

| Métrique | Résultat |
|---|---|
| Précision | 75 % (en baisse) |
| Rappel | 33 % (inchangé) |

**Résultat honnête : l'enrichissement du prompt n'a pas amélioré le rappel, et a même fait apparaître un faux positif supplémentaire** (détection de gluten hallucinée sur un houmous n'en contenant pas). Le mot « sésame », pourtant présent tel quel dans le texte, n'est toujours pas relié à la catégorie attendue.

### Interprétation

Le facteur limitant n'est pas la formulation du prompt mais **la capacité du modèle 3B lui-même** à appliquer une instruction de correspondance sur une liste de 14 catégories avec leurs synonymes. C'est une limite honnête à documenter plutôt qu'à masquer.

## 7. Monitorage disponible (Ollama)

| Commande | Usage |
|---|---|
| `ollama ps` | Modèle actuellement chargé en mémoire, empreinte mémoire, répartition CPU/GPU, durée avant déchargement automatique |
| `ollama list` / `GET /api/tags` | Modèles disponibles localement, taille, quantification, taille de contexte |

Constat d'exécution : `llama3.2:3b` occupe 3,1 Go, s'exécute à 78 % CPU / 22 % GPU sur ce poste. Ce monitorage basique suffit au stade du POC ; un monitorage applicatif complet (précision dans le temps, latence, alertes) sera mis en place en S7 (C11).

## 8. Conclusion et recommandation pour la suite

Le service est **installé, accessible et fonctionnellement intégrable** (C8 satisfait) : le POC prouve la faisabilité technique de la connexion. En revanche, la **qualité d'extraction à elle seule est insuffisante pour un cas d'usage sécuritaire** (un allergène raté a des conséquences réelles pour l'utilisateur).

**Recommandation retenue pour la conception de l'API IA (S6)** : ne pas se reposer uniquement sur le modèle. Coupler l'extraction par IA à une **recherche par mots-clés déterministe** (la liste `SYNONYMES_ALLERGENES` déjà écrite pour le prompt sert aussi de dictionnaire de correspondance directe) et retenir l'**union des deux détections** plutôt que le seul résultat du modèle — un faux positif occasionnel est préférable à un allergène non signalé. Cette approche hybride (règles + IA) sera implémentée et testée en S6-S7, avec un suivi de sa précision/rappel dans le monitoring du modèle (C11, S7).
