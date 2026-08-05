# Prototype applicatif (C10) — S6

## 1. Présentation

[`app/frontend/prototype.py`](../../app/frontend/prototype.py) : application Streamlit démontrant l'intégration de l'API IA (S6) et de l'API Data (Bloc 1) dans une interface utilisateur. Ce n'est pas l'application finale (Bloc 3, S9) : pas de compte ni de persistance du profil, celui-ci est saisi à chaque session.

## 2. Installation et lancement

```bash
cd app
py -m pip install -r requirements.txt
py -m streamlit run frontend/prototype.py
```

Prérequis : la stack Docker (`docker compose up -d` à la racine) et Ollama (`ollama serve`) doivent être démarrés — le prototype consomme les deux API, il ne contient aucune logique métier propre.

## 3. Intégration des API

| Fonctionnalité | Endpoint(s) exploité(s) |
|---|---|
| Référentiel des allergènes (profil) | `GET /allergenes` (API Data) |
| Recherche de produit | `GET /produits` (API Data) |
| Recherche de recette | `GET /recettes` (API Data) |
| Analyse de compatibilité — produit | `POST /analyser/produit/{code_barres}` (API IA) |
| Analyse de compatibilité — recette | `POST /analyser/recette/{id_recette}` (API IA) |
| Analyse de compatibilité — texte libre | `POST /analyser/texte` (API IA) |

**Authentification et renouvellement** : un jeton est obtenu séparément pour chaque API (deux jetons distincts, deux services), mis en cache dans `st.session_state`. En cas de réponse `401` (jeton expiré), le jeton est invalidé et renouvelé automatiquement avant une nouvelle tentative (voir `_appel_api`).

## 4. Adaptations d'interface (accessibilité)

- Le statut de compatibilité n'est **jamais porté par la seule couleur** : icône + libellé texte (`✅ Compatible` / `⚠️ À risque` / `⛔ Incompatible`), conformément à [US4](../01-cadrage/user-stories.md#us4--alerte-allergènes-et-score-de-compatibilité).
- L'avertissement produit (« ne constitue pas un avis médical ») est affiché en permanence en tête de page.
- Le détail de la détection (IA vs mots-clés, justification) est exposé dans une section repliable, pour la transparence de la décision algorithmique sans surcharger l'affichage principal.

## 5. Tests d'intégration

[`app/tests/test_integration.py`](../../app/tests/test_integration.py) — appelle la **vraie** stack (pas de mock), contrairement aux tests unitaires de l'API IA :

```bash
cd app
py -m pytest tests/test_integration.py -v
# 9 passed in 76s (l'analyse IA prend 15-30s par appel)
```

Couvre tous les endpoints consommés par le prototype : authentification (2 API), listing produits/recettes/allergènes, analyse de texte/produit/recette, et le cas 404.

## 6. Bugs découverts et corrigés pendant les tests manuels

Le prototype a été testé manuellement dans un navigateur (parcours complet : sélection d'un profil, recherche d'un produit, analyse) avant d'être considéré fonctionnel — c'est cet exercice qui a révélé deux problèmes réels, corrigés avant la livraison plutôt que découverts plus tard :

1. **Timeout trop court.** Le premier essai a échoué avec `Read timed out (timeout=30)` : une inférence Ollama après rechargement à froid du modèle peut dépasser 30 secondes. Corrigé en portant le timeout des appels d'analyse à 90s et en affichant un `st.spinner` explicite (« peut prendre jusqu'à une minute »).
2. **Angle mort multilingue.** Le produit test choisi (« 3x Steinofen-Pizza Salami ») a des ingrédients en **allemand** (« Milch », « Weizenmehl »). Ni le modèle ni le dictionnaire de mots-clés (FR/EN seulement) n'ont détecté le lait : le prototype affichait « Compatible » pour un profil allergique au lait — un faux négatif de sécurité. Corrigé en étendant `SYNONYMES_ALLERGENES` avec les termes allemands les plus courants (voir `ai-service/common/allergenes.py`). Le correctif a immédiatement révélé un second bug : le terme allemand ajouté pour « œuf » (« ei ») est trop court et déclenche un faux positif par sous-chaîne dans des mots sans rapport (« Speisesalz », « Reifekulturen ») — retiré, remplacé par des formes plus longues et sûres (« eier », « eiklar »).
   **Limite assumée et documentée** : la couverture multilingue reste partielle (FR/EN/DE) ; l'espagnol, l'italien, etc. ne sont pas couverts à ce stade — mentionné comme axe d'amélioration pour le monitoring du modèle (C11, S7).

Ce constat renforce, avec un cas réel plutôt que théorique, la décision prise au POC (S5) de ne jamais se reposer sur la seule IA pour un cas d'usage sécuritaire.
