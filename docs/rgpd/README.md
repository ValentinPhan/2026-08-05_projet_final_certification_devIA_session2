# RGPD

À rédiger en S3, en même temps que la base de données ([`data-pipeline/db`](../../data-pipeline/db)) :

- `registre-traitements.md` — registre des traitements de données personnelles (comptes utilisateurs, profil allergène, historique d'analyses) (C4)
- `procedures-tri.md` — procédures de tri/purge des données personnelles inutiles ou trop anciennes (C4)

Point d'attention majeur : le profil allergène/intolérance est une **donnée de santé**, catégorie particulière au sens de l'**article 9 du RGPD**, nécessitant un consentement explicite distinct et des mesures de sécurité renforcées (chiffrement, voir `docs/01-cadrage/architecture.md`). Le choix d'un service IA exécuté en local (Ollama, voir [docs/03-bloc2-ia/benchmark-services-ia.md](../03-bloc2-ia/benchmark-services-ia.md)) pour traiter cette donnée est un argument de conformité par conception (privacy by design) à documenter ici.
