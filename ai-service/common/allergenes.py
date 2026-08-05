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

# Synonymes/formes ingredients par allergene. Constitue et corrige de facon
# iterative a partir de cas reels plutot que par anticipation - voir
# docs/03-bloc2-ia/tests-modele.md pour l'historique complet :
#
# - Ajout initial (POC S5) : le modele ne reliait pas toujours un synonyme
#   ("tahini") a la categorie officielle ("Graines de sesame").
# - Ajout allemand (prototype S6) : un produit dont les ingredients sont en
#   allemand ("Milch") passait a tort pour "compatible".
# - Ajout anglais + retraits de precision (monitoring S7, via le jeu de
#   donnees de reference `golden_dataset.py`) : plusieurs mots anglais
#   basiques manquaient ("wheat", "milk", "egg", "fish", "soy", "sulphite"
#   orthographe britannique), et plusieurs synonymes trop generiques
#   provoquaient de faux positifs : "farine" seul (present dans "farine
#   d'amande", sans gluten), "beurre"/"butter" seul (present dans "beurre de
#   cacao", sans lait), "noix" seul (present dans "noix de muscade" et "noix
#   de coco", sans lien avec les fruits a coque allergenes). Ces trois
#   synonymes ambigus ont ete retires plutot que corriges par une regle
#   ad hoc : limite de precision assumee et documentee (voir
#   docs/03-bloc2-ia/tests-modele.md) plutot que rustine fragile.
#
# Couverture linguistique assumee comme incomplete au-dela du FR/EN/DE
# (espagnol, italien, etc. non couverts a ce stade).
SYNONYMES_ALLERGENES: dict[str, list[str]] = {
    "Gluten (cereales)": [
        "ble", "froment", "orge", "seigle", "avoine", "epeautre", "amidon de ble", "gluten", "farine de ble",
        "wheat", "barley", "rye", "oat", "malt",  # anglais
        "weizen", "weizenmehl", "weizenstarke", "roggen", "gerste", "hafer",  # allemand
    ],
    "Crustaces": [
        "crevette", "crabe", "homard", "langoustine", "langouste", "crustace",
        "shrimp", "prawn", "crab", "lobster", "crayfish",  # anglais
    ],
    "Oeufs": [
        "oeuf", "ovoproduit", "albumine", "lysozyme",
        "egg", "albumin",  # anglais
        "eier", "eiklar", "eigelb", "vollei",  # allemand ("ei" seul exclu, voir note ci-dessous)
    ],
    "Poissons": [
        "poisson", "anchois", "thon", "saumon", "gelatine de poisson",
        "fish", "anchovy", "tuna", "salmon", "cod",  # anglais
        "fisch",  # allemand
    ],
    "Arachides": [
        "arachide", "cacahuete", "huile d'arachide",
        "peanut", "groundnut",  # anglais
        "erdnuss",  # allemand
    ],
    "Soja": [
        "soja", "lecithine de soja", "sauce soja", "tofu", "edamame",
        "soy", "soya", "soybean", "soy lecithin",  # anglais
        "sojabohne",  # allemand
    ],
    "Lait": [
        "lait", "lactose", "caseine", "proteines de lait", "petit-lait", "creme", "fromage",
        "milk", "whey", "cream", "cheese", "butter",  # anglais
        "milch", "milchpulver", "molke", "kase", "sahne", "edamer", "joghurt",  # allemand
    ],
    "Fruits a coque": [
        "amande", "noisette", "noix de cajou", "pistache", "noix de pecan",
        "noix du bresil", "noix de macadamia", "cerneau de noix", "noix de grenoble",
        "almond", "hazelnut", "walnut", "cashew", "pistachio", "pecan", "brazil nut", "macadamia",  # anglais
        "mandel", "haselnuss",  # allemand
    ],
    "Celeri": ["celeri", "sellerie", "celery"],
    "Moutarde": ["moutarde", "senf", "mustard"],
    "Graines de sesame": [
        "sesame", "tahini", "pate de sesame", "puree de sesame", "huile de sesame",
        "sesame seed", "sesame oil",  # anglais (memes racines que le francais)
        "sesam",  # allemand
    ],
    "Anhydride sulfureux et sulfites": [
        "sulfite", "anhydride sulfureux", "metabisulfite", "so2",
        "sulphite", "sulphur dioxide", "sulfur dioxide", "metabisulphite",  # anglais (orthographe britannique et americaine)
        "sulfit",  # allemand
    ],
    "Lupin": ["lupin", "lupine", "lupini"],
    "Mollusques": [
        "moule", "huitre", "escargot", "calmar", "poulpe", "coquille saint-jacques", "mollusque",
        "mussel", "oyster", "squid", "octopus", "snail", "scallop", "clam",  # anglais
    ],
}
