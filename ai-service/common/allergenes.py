"""Referentiel des 14 allergenes officiels (reglement UE 1169/2011) et leurs
synonymes/formes usuelles, partages par le POC (S5) et l'API IA (S6).

Identique au referentiel seede dans data-pipeline/db/schema.sql (memes
libelles) : ai-service duplique volontairement cette liste plutot que de
l'importer depuis data-pipeline (voir docs/01-cadrage/architecture.md, les
composants restent independants et ne communiquent que par API REST).
"""
from __future__ import annotations

ALLERGENES_REFERENTIEL = [
    "Gluten (cereales)",
    "Crustaces",
    "Oeufs",
    "Poissons",
    "Arachides",
    "Soja",
    "Lait",
    "Fruits a coque",
    "Celeri",
    "Moutarde",
    "Graines de sesame",
    "Anhydride sulfureux et sulfites",
    "Lupin",
    "Mollusques",
]

# Synonymes/formes ingredients par allergene. Ajoutes suite au POC (S5) qui a
# montre que le modele ne reliait pas toujours un synonyme ("tahini") a la
# categorie officielle - voir docs/03-bloc2-ia/poc.md. Servent ici a la fois
# de contexte pour le prompt IA et de dictionnaire pour la recherche par
# mots-cles deterministe (voir ai-service/api_ia/extraction.py).
#
# Couverture multilingue partielle (FR/EN + termes allemands les plus
# courants) : ajoutee suite a un test du prototype (S6) sur un produit
# allemand ("3x Steinofen-Pizza Salami") dont l'ingredient "Milch" (lait)
# n'etait detecte ni par le modele ni par la recherche par mots-cles
# FR/EN, provoquant un faux "compatible" pour un profil allergique au
# lait - voir docs/03-bloc2-ia/prototype.md. Open Food Facts etant une
# base mondiale, la couverture au-dela du FR/EN/DE reste une limite
# connue (espagnol, italien, etc. non couverts a ce stade).
SYNONYMES_ALLERGENES: dict[str, list[str]] = {
    "Gluten (cereales)": [
        "ble", "froment", "orge", "seigle", "avoine", "epeautre", "farine", "amidon de ble", "gluten",
        "weizen", "weizenmehl", "weizenstarke", "roggen", "gerste", "hafer",  # allemand
    ],
    "Crustaces": ["crevette", "crabe", "homard", "langoustine", "langouste", "crustace"],
    # "ei" (allemand, oeuf) volontairement exclu : trop court, matche par erreur
    # dans des mots sans rapport ("Speisesalz", "Reifekulturen") avec une simple
    # recherche de sous-chaine - constate lors du test du prototype (S6).
    "Oeufs": ["oeuf", "ovoproduit", "albumine", "lysozyme", "eier", "eiklar", "eigelb", "vollei"],
    "Poissons": ["poisson", "anchois", "thon", "saumon", "gelatine de poisson", "fisch"],
    "Arachides": ["arachide", "cacahuete", "huile d'arachide", "erdnuss"],
    "Soja": ["soja", "lecithine de soja", "sauce soja", "tofu", "edamame", "sojabohne"],
    "Lait": [
        "lait", "lactose", "caseine", "proteines de lait", "petit-lait", "whey", "beurre", "creme", "fromage",
        "milch", "milchpulver", "molke", "kase", "sahne", "butter", "edamer", "joghurt",  # allemand
    ],
    "Fruits a coque": [
        "amande", "noisette", "noix de cajou", "pistache", "noix de pecan",
        "noix du bresil", "noix de macadamia", "noix", "nuss", "haselnuss", "mandel",
    ],
    "Celeri": ["celeri", "sellerie"],
    "Moutarde": ["moutarde", "senf"],
    "Graines de sesame": ["sesame", "tahini", "pate de sesame", "puree de sesame", "huile de sesame", "sesam"],
    "Anhydride sulfureux et sulfites": ["sulfite", "anhydride sulfureux", "metabisulfite", "so2", "sulfit"],
    "Lupin": ["lupin", "lupine"],
    "Mollusques": ["moule", "huitre", "escargot", "calmar", "poulpe", "coquille saint-jacques", "mollusque"],
}
