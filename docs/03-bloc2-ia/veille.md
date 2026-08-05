# Veille technique et réglementaire (C6) — S4

## 1. Thématique de veille

Deux axes, tous deux directement mobilisés par NutriScan IA :

- **Réglementaire** : traitement des données de santé (profil allergène, RGPD article 9) et réglementation de la sécurité alimentaire/allergènes (règlement INCO 1169/2011).
- **Technique** : état de l'art des modèles d'IA exécutables en local (candidat retenu pour le Bloc 2, voir [`benchmark-services-ia.md`](benchmark-services-ia.md)), pour rester en phase avec un écosystème qui évolue vite.

## 2. Organisation de la veille

- **Récurrence** : créneau hebdomadaire d'une heure, chaque début de semaine (aligné sur le rituel agile de `docs/01-cadrage/backlog.md`), en plus d'une vérification rapide (10 min) en milieu de semaine sur les sources techniques.
- **Rôle** (projet solo) : auto-portée par le développeur, qui journalise la synthèse dans ce fichier au fil des semaines plutôt que de la garder informelle.

## 3. Outils de collecte et de partage

| Besoin | Outil retenu | Justification |
|---|---|---|
| Agrégation des flux | Script Python (`ai-service/veille/aggregate_veille.py`, `feedparser`) sur des flux **RSS/Atom publics** | Gratuit, sans compte ni clé, reproductible et versionné avec le projet — cohérent avec la contrainte budgétaire (0 €) et avec le choix, fait dès le cadrage, de n'exiger aucune inscription à un service tiers |
| Partage des synthèses | Ce document Markdown, versionné dans le dépôt Git | Accessible sans outil propriétaire, structuré par titres hiérarchiques, lisible par un lecteur d'écran — voir section 6 |

Alternative écartée : un agrégateur grand public (Feedly, Inoreader) aurait apporté une interface plus riche, mais nécessite la création d'un compte — écarté pour rester cohérent avec la contrainte du projet.

## 4. Sources retenues et évaluation de fiabilité

| Source | Thème | Flux | Évaluation de fiabilité |
|---|---|---|---|
| CNIL — Actualités | Réglementaire | `cnil.fr/fr/rss.xml` | Autorité administrative indépendante française, auteur institutionnel identifié, publications datées et sourcées, aucun intérêt commercial |
| EFSA — News | Réglementaire | `efsa.europa.eu/en/all/rss` | Agence de l'Union européenne, avis scientifiques signés par des panels d'experts nommés, procédure de publication tracée |
| Ollama — Releases (GitHub) | Technique | `github.com/ollama/ollama/releases.atom` | Dépôt officiel du projet (organisation vérifiée sur GitHub), changelog détaillé et daté à chaque version |
| Hugging Face — Blog | Technique | `huggingface.co/blog/feed.xml` | Plateforme de référence du secteur (auteurs identifiés par organisation/compte), forte notoriété, contenu daté |

Ces 4 sources ont été retenues après avoir écarté des agrégateurs génériques (ex. actualité tech grand public) dont l'auteur et le niveau d'expertise ne sont pas systématiquement identifiables — critère de fiabilité prioritaire pour une veille réglementaire.

## 5. Synthèse — semaine du 2026-08-05

Extraits collectés automatiquement le 2026-08-05 (voir `ai-service/data/raw/veille/veille_2026-08-05.json`, non versionné — données brutes reproductibles en relançant le script).

### Réglementaire

- **CNIL** publie deux webinaires (juillet 2026) directement liés à notre périmètre : la mise à jour des **méthodologies de référence santé (MR-001/MR-003)** et un nouveau téléservice pour les demandes d'autorisation « santé et recherche ». Ces MR encadrent le traitement de données de santé à des fins d'étude — pertinent pour documenter, si le projet dépassait le cadre pédagogique, une éventuelle formalité CNIL liée au profil allergène. **Action** : noter la référence MR-001/MR-003 dans le [registre des traitements](../rgpd/registre-traitements.md) comme point de vigilance pour une mise en production réelle.
- **EFSA** publie cette semaine des avis sur des « novel foods » (nouveaux aliments) plutôt que sur l'étiquetage des allergènes à proprement parler. Le point notable est que ces avis sont rendus par le panel **NDA (Nutrition, Novel Foods and **Food Allergens**)** — confirmation que l'EFSA est la bonne source institutionnelle à suivre sur la durée du projet pour toute évolution du référentiel des 14 allergènes, même si aucune évolution réglementaire directe n'est publiée cette semaine.

### Technique

- **Ollama** a publié 4 versions en une dizaine de jours (v0.32.3 à v0.32.6), avec un rythme de développement actif. Deux points concrets pour le Bloc 2 :
  - Le format de streaming de l'endpoint `/v1/chat/completions` a été aligné sur le **format natif d'OpenAI** (rôle uniquement sur le premier chunk, `finish_reason` séparé). **Action retenue pour S6** : utiliser directement le client Python `openai` pointé sur `http://localhost:11434/v1` plutôt qu'un client HTTP maison, ce qui simplifie l'intégration côté `ai-service/api_ia/`.
  - Support GPU élargi (CUDA sur Windows ARM64) : confirme la portabilité de la solution sur des postes de développement variés, argument supplémentaire pour le choix retenu dans le benchmark.
- **Hugging Face Blog** met en avant *« Deploy local agents everywhere with LFM2.5-2.6B »* : un modèle compact conçu spécifiquement pour l'inférence locale/embarquée. **Action** : à évaluer en S5 comme alternative légère si le modèle initialement pressenti pour le POC s'avère trop lourd pour le poste de développement.
- Un article Hugging Face documente une intrusion technique visée sur un agent d'un « frontier lab » en juillet 2026 — rappel utile pour la section sécurité (OWASP) du service IA à développer en S6 : ne jamais exposer directement les capacités d'exécution du modèle sans validation des entrées côté API.

## 6. Accessibilité de la diffusion

Ce document respecte les recommandations d'accessibilité (RGAA/WCAG) applicables à un document texte : titres hiérarchiques structurant la navigation, tableaux avec en-têtes explicites, liens explicites (pas de « cliquez ici »), pas d'information portée uniquement par la couleur ou la mise en forme.
