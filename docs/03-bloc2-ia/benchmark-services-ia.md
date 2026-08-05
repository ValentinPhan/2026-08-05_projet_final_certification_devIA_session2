# Benchmark des services d'intelligence artificielle (C7) — S4

## 1. Reformulation du besoin

NutriScan IA a besoin d'un service capable, à partir d'un **texte libre** (liste d'ingrédients d'un produit Open Food Facts ou d'une recette scrapée, en français ou en anglais), d'**extraire les allergènes et ingrédients pertinents** avec un niveau de confiance suffisant pour être comparés ensuite au profil alimentaire de l'utilisateur.

Contraintes fixées dès le cadrage (voir [cahier-des-charges.md](../01-cadrage/cahier-des-charges.md)) :

- **Budget nul** : aucun service payant à l'usage ne peut être retenu comme solution par défaut.
- **Aucune création de compte** : contrainte explicite du projet.
- **Confidentialité par conception** : le résultat de l'extraction est ensuite croisé avec une donnée de santé (le profil allergène de l'utilisateur, RGPD article 9) — même si ce croisement a lieu en dehors de l'appel IA lui-même, minimiser le nombre de tiers impliqués dans la chaîne reste un principe de précaution retenu.
- **Reproductibilité** : la solution doit fonctionner sur un poste de développement standard, sans dépendre d'un abonnement susceptible de changer de conditions.
- **Transparence environnementale** : à défaut d'un budget carbone formel, la transparence du fournisseur sur son empreinte est un critère de choix explicite (cohérent avec l'éco-conception documentée dans [architecture.md](../01-cadrage/architecture.md)).

## 2. Services étudiés vs non étudiés

**Étudiés en détail** (section 3) : Ollama (local), OpenAI API, Mistral API, Groq.

**Identifiés mais non étudiés en détail**, avec raison explicite :

| Service | Raison de l'exclusion de l'étude approfondie |
|---|---|
| Hugging Face Inference API | Redondant avec Ollama pour l'exécution de modèles open-source ; n'apporte pas d'avantage suffisant pour justifier la création d'un compte/token que Ollama permet d'éviter |
| LM Studio | Alternative locale équivalente à Ollama sur les critères qui comptent ici (gratuit, sans compte, exécution locale) ; non étudiée en profondeur une fois Ollama confirmé installé et fonctionnel sur le poste de développement (S4), mais retenue comme **solution de repli documentée** si Ollama posait un problème bloquant en S5 |
| Azure AI Foundry / AWS Bedrock | Offres cloud entreprise, écartées d'emblée : nécessitent un compte facturé et sont surdimensionnées pour le budget (0 €) et l'échelle d'un projet pédagogique |

## 3. Grille de comparaison détaillée

| Critère | **Ollama** (local) | OpenAI API | Mistral API | Groq |
|---|---|---|---|---|
| **Adéquation fonctionnelle** | Bonne pour l'extraction d'entités avec des modèles 3B-8B (Llama 3.2, Mistral 7B, Qwen2.5) ; qualité à confirmer par le POC (S5) | Excellente, multilingue, très documentée | Bonne, spécialisé multilingue FR/EN | Bonne (modèles open-source hébergés : Llama 3.x), débit très élevé (280 à >1000 tokens/s selon le modèle) |
| **Contraintes techniques** | RAM/CPU suffisants pour un modèle quantifié (8-16 Go recommandés), GPU optionnel ; **déjà installé sur le poste de développement** (v0.32.5 confirmée en S4) | Compte + clé API requis ; connexion Internet à chaque requête | Compte + clé API requis | Compte + clé API requis |
| **Éco-responsabilité** | Aucun rapport de cycle de vie publié (logiciel, pas un service géré) ; pas de nouvelle infrastructure dédiée, exécution sur du matériel déjà possédé | Transparence jugée faible par un tiers indépendant (score climat 23/100, DitchCarbon) ; seule donnée disponible = déclaration non vérifiée du CEO (~0,34 Wh/requête ChatGPT), non comparable méthodologiquement | **La plus transparente du marché** : première analyse de cycle de vie (ACV) d'un LLM publiée (Mistral Large 2, juillet 2025), réalisée avec l'ADEME et Carbone 4, conforme ISO 14040/44 et méthodologie Frugal AI (AFNOR) — 1,14 gCO2e et 45 mL d'eau pour une réponse de 400 tokens | Aucune donnée environnementale publiée identifiée |
| **Confidentialité** | **Totale** : aucune donnée ne quitte la machine | Envoi à un tiers basé aux États-Unis | Envoi à un tiers (hébergement UE possible selon l'offre) | Envoi à un tiers basé aux États-Unis |
| **Coût** | **0 €** | Facturé à l'usage (consulter la page tarifaire officielle au moment de l'implémentation) | Facturé à l'usage | Très compétitif (dès 0,05 $/M tokens en entrée sur les petits modèles, jusqu'à 10-20x moins cher qu'OpenAI sur des modèles équivalents), mais non nul |

Sources des données environnementales : rapport ACV Mistral AI (juillet 2025, avec ADEME/Carbone 4, revu par Resilio et Hubblo) ; analyse indépendante DitchCarbon sur la transparence climatique d'OpenAI ; déclaration publique du CEO d'OpenAI (juin 2025). Ces chiffres ne sont pas directement comparables entre eux (méthodologies différentes) — c'est justement le manque d'un référentiel commun qui rend la **transparence elle-même** (publiée ou non) un critère de choix pertinent, indépendamment des valeurs absolues.

## 4. Conclusion

| | Répond au besoin ? | Avantages | Inconvénients |
|---|---|---|---|
| **Ollama** | ✅ Oui — **solution retenue** | Zéro coût, zéro compte, confidentialité totale, déjà installé et fonctionnel | Qualité d'extraction à valider par le POC (S5), performance dépendante du matériel local |
| Mistral API | ⚠️ Partiellement | Le plus transparent sur l'impact environnemental, entreprise européenne | Nécessite un compte (contrainte projet non respectée), donnée envoyée à un tiers |
| Groq | ⚠️ Partiellement | Débit et rapport qualité/prix excellents pour du cloud | Nécessite un compte, aucune transparence environnementale publiée, coût non nul |
| OpenAI API | ❌ Non retenu pour ce projet | Qualité et documentation de référence | Nécessite un compte, coût, transparence environnementale jugée faible par un tiers indépendant |

**Ollama est le seul service qui satisfait simultanément toutes les contraintes du projet** (budget nul, aucune création de compte, confidentialité totale). Les trois services cloud étudiés (OpenAI, Mistral, Groq) répondraient chacun techniquement au besoin fonctionnel — et seraient à reconsidérer si le projet sortait du cadre pédagogique et acceptait un budget et un compte fournisseur, Mistral se distinguant alors nettement sur la transparence environnementale. Le paramétrage effectif d'Ollama et le choix du modèle précis font l'objet du POC en S5 (voir [`poc.md`](poc.md)).

Sources :
- [Mistral AI publie l'analyse de cycle de vie de ses modèles](https://www.solutions-numeriques.com/mistral-ai-detaille-lempreinte-environnementale-de-ses-modeles-dia/)
- [French Mistral AI sets new environmental standard with comprehensive LCA report](https://www.hhc.earth/knowledge-base/articles/french-mistral-ai-sets-new-environmental-standard-with-comprehensive-lca-report)
- [Groq API Pricing 2026](https://www.cloudzero.com/blog/groq-pricing/)
- [What kind of environmental impacts are AI companies disclosing? (Hugging Face)](https://huggingface.co/blog/sasha/environmental-impact-disclosures)
