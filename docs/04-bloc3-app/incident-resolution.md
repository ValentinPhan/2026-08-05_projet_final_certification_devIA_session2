# Résolution d'incidents techniques (C21) — S11

Deux pannes de dépendance ont été **réellement simulées** (arrêt effectif du conteneur/processus concerné, pas une lecture de code) pour vérifier le comportement de l'application en conditions dégradées, conformément à US9 (« transparence en cas d'indisponibilité »). Les deux ont révélé des bugs réels, corrigés puis reconfirmés par un nouveau cycle panne → rétablissement.

## Incident 1 — API Data indisponible

**Scénario** : `docker stop nutriscan-api-data` pendant l'utilisation de l'application.

**Constat côté API IA** (déjà en place, confirmé) : `api_ia` répond `502` avec un message explicite (« API Data indisponible : ... ») — comportement correct, hérité de S6.

**Constats côté frontend (`app/frontend/main.py`) — 3 bugs réels trouvés** :

| # | Page | Bug | Conséquence |
|---|---|---|---|
| 1 | Rechercher un produit / une recette | `_appel_service(...) or []` confondait un appel en échec (`None`) avec un résultat réellement vide | Après l'erreur déjà affichée, un second message « Aucun produit trouvé pour ce filtre » laissait croire à un catalogue vide plutôt qu'à une panne |
| 2 | Historique | Même confusion via `_appel_backend` | « Aucune analyse enregistrée » affiché à tort pendant une panne |
| 3 | `_appel_backend` (fonction partagée) | Une erreur HTTP ≥400 renvoyée par le backend (hors 401) ne déclenchait **aucun** message | Panne silencieuse pour tout appelant de cette fonction |
| 4 (le plus grave) | Mon profil | Si le chargement initial du profil échouait, un profil **vide** était mis en cache pour la session | Un clic sur « Enregistrer » sans rien cocher aurait **écrasé silencieusement le vrai profil allergène sauvegardé** — donnée de santé perdue par une panne transitoire |

**Corrections** : distinction explicite `None` (échec, déjà signalé) vs liste/résultat vide dans les trois pages concernées ; message d'erreur générique ajouté dans `_appel_backend` pour toute réponse ≥400 ; page Profil bloquée (message d'erreur, formulaire non affiché) plutôt que mise en cache d'un état vide en cas d'échec de chargement.

**Vérification** : panne provoquée réellement (conteneur arrêté), page Historique visitée pour la première fois dans la session → message d'erreur clair affiché, aucune mention trompeuse d'historique vide. Conteneur redémarré → nouvelle visite de la page → « Aucune analyse enregistrée pour l'instant » correctement affiché (résultat réellement vide cette fois).

## Incident 2 — Ollama (modèle IA) indisponible

**Scénario** : arrêt réel du processus Ollama pendant une analyse.

**Constat (avant correctif)** : `POST /analyser/texte` renvoyait **500 Internal Server Error**, sans aucun résultat — y compris pour le filet de sécurité par mots-clés (`detecter_par_mots_cles`), qui ne nécessite pourtant aucun réseau. Cause : `analyser_texte()` (`ai-service/api_ia/extraction.py`) appelait le modèle **avant** la recherche par mots-clés, sans gestion d'exception : une erreur de connexion à Ollama (`openai.APIConnectionError`) interrompait la fonction entière avant que la recherche déterministe n'ait pu s'exécuter.

C'est le bug le plus critique trouvé dans ce projet : l'architecture hybride IA + mots-clés (S6) a précisément été conçue pour qu'un allergène explicitement nommé ne soit jamais manqué — une panne totale du modèle annulait entièrement cette garantie plutôt que de dégrader proprement.

**Correction** (`extraction.py`) : la recherche par mots-clés est désormais calculée **en premier**, indépendamment du modèle ; l'appel au modèle est encadré par un `try/except OpenAIError` ; en cas d'échec, l'analyse se poursuit en mode dégradé (mots-clés seuls) avec un champ `ia_disponible: false` explicite et une justification claire, jamais un échec silencieux. Le frontend affiche un avertissement (`st.warning`, annoncé aux technologies d'assistance) dès que `ia_disponible` est `false`.

**Vérification** (cycle complet, en conditions réelles) :

| Étape | Résultat |
|---|---|
| Avant correctif, Ollama coupé | `500`, aucune détection |
| Après correctif, Ollama toujours coupé | `200`, `ia_disponible: false`, allergènes tout de même détectés par mots-clés (« Lait », « Graines de sesame »), statut correct (« incompatible ») |
| Ollama redémarré | `200`, `ia_disponible: true`, fonctionnement normal (IA + mots-clés) |
| Frontend, Ollama coupé | Bannière « ⚠️ Service IA temporairement indisponible... » affichée, résultat quand même exploitable |

**Tests automatisés ajoutés** (`ai-service/api_ia/tests/test_extraction.py`) : le scénario de panne (exception `APIConnectionError` simulée) est rejoué en test unitaire pour éviter toute régression future — 10/10 tests passent, dont les deux nouveaux (`test_analyser_texte_degrade_sur_mots_cles_si_ia_indisponible`, `test_analyser_texte_ia_disponible_a_true_en_fonctionnement_normal`).

## Portée transverse : Bloc 2 touché depuis un exercice Bloc 3

Le correctif de l'incident 2 modifie `ai-service/` (Bloc 2, compétences déjà validées en S6-S8). Choix assumé : un incident de production ne respecte pas les frontières entre blocs de compétences, et la découverte de ce bug n'aurait été possible qu'en exploitant réellement l'application complète (Bloc 3) — exactement le rôle d'un exercice de gestion d'incident. Même logique déjà appliquée en S9 (enrichissement du Bloc 1 nécessaire au score nutritionnel du Bloc 3).

## Lien avec US9

Les deux incidents referment explicitement le backlog restant sur **US9 — Transparence en cas d'indisponibilité** ([backlog.md](../01-cadrage/backlog.md)) : dans les deux cas, l'application n'affiche plus jamais un état trompeur (ni « compatible » par défaut, ni « aucun résultat » masquant une panne) et informe toujours clairement l'utilisateur, avec un message annoncé aux technologies d'assistance.
