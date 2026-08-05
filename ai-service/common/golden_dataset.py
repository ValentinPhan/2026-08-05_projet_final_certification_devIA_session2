"""Jeu de donnees de reference ("golden dataset") pour l'evaluation du modele
d'extraction d'allergenes (competences C11 - monitoring, C12 - tests).

Ces 11 cas sont des textes REELS (produits Open Food Facts et recettes
scrapees, deja en base via le Bloc 1), fixes ici plutot que recuperes en
direct depuis l'API Data : un jeu d'evaluation doit rester stable dans le
temps pour permettre de comparer deux executions (avant/apres une
modification du prompt ou du dictionnaire de synonymes), ce qu'une source
vivante (la base, susceptible d'evoluer) ne garantit pas.

Chaque cas a ete choisi pour ce qu'il apporte a la couverture de test :
- cas multi-allergenes (plusieurs detections attendues a la fois)
- cas "piege" (un produit affiche "gluten free" mais contient d'autres
  allergenes - verifie qu'on se fie au texte reel, pas au nom du produit)
- cas negatifs propres (aucun allergene, y compris un texte multilingue)
- cas de precision (lecithine de *tournesol*, qui ne doit pas declencher
  une fausse alerte "Soja")
- le cas reel qui a revele le bug multilingue du prototype (S6, produit
  allemand) - sert de test de non-regression
- deux recettes (pas seulement des produits), dont une (Ratatouille) sans
  aucun allergene officiel.

`allergenes_attendus` provient du referencement Open Food Facts pour les
produits (lui-meme non infaillible - voir limite documentee dans
docs/03-bloc2-ia/poc.md) ou d'une lecture manuelle des ingredients pour les
recettes.
"""
from __future__ import annotations

CAS_EVALUATION: list[dict[str, object]] = [
    {
        "id": "pizza_allemande_multilingue",
        "description": "Produit allemand (Milch/Weizenmehl) - a revele un angle mort multilingue au prototype S6",
        "texte": (
            "Weizenmehl, Tomatenpüree, Wasser, 11,4 % Edamer (Milch, Speisesalz, "
            "mikrobielles Lab, Starterkulturen), 9,1 % Salami (Schweinefleisch, Speck, "
            "Speisesalz, Gewürzextrakte, Dextrose, Glukosesirup, Antioxidationsmittel: "
            "Extrakt aus Rosmarin, Natriumisoascorbat; Gewürze, Zucker, Konservierungsstoff: "
            "Natriumnitrit; Reifekulturen, Rauch), Rapsöl, Hefe, Speisesalz, Stärke, "
            "Weizenstärke, Oregano, Dextrose, Gewürze"
        ),
        "allergenes_attendus": ["Gluten (cereales)", "Lait"],
    },
    {
        "id": "houmous_sesame_fr",
        "description": "Cas reel du POC (S5) : le mot 'sesame' est present tel quel, teste le filet de securite mots-cles",
        "texte": "Eau, pois chiche* (28%), huile d'olive*, purée de sésame*, jus de citron*, ail*, sel, cumin*",
        "allergenes_attendus": ["Graines de sesame"],
    },
    {
        "id": "biscuit_multi_allergenes",
        "description": "Trois allergenes attendus simultanement",
        "texte": (
            "wheat flour (with added calcium carbonate, iron, niacin, thiamin), "
            "raspberry flavoured apple jam (27%) (glucose-fructose syrup, apples (39%) "
            "(apple, preservative (sodium metabisulphite)), sugar, humectant (glycerol), "
            "acid (citric acid), acidity regulator (sodium citrates), flavourings, "
            "colours (anthocyanins, annatto), gelling agent (pectin)), palm oil, sugar, "
            "whey or whey derivatives (milk), partially inverted sugar syrup, raising "
            "agents (ammonium bicarbonate, sodium bicarbonate), salt, flavourings"
        ),
        "allergenes_attendus": ["Anhydride sulfureux et sulfites", "Gluten (cereales)", "Lait"],
    },
    {
        "id": "lait_uht_simple",
        "description": "Cas trivial (un seul allergene, texte tres court) - sert de garde-fou de base",
        "texte": "Lait demi-écrémé stérilisé U.H.T.",
        "allergenes_attendus": ["Lait"],
    },
    {
        "id": "piege_gluten_free",
        "description": "Produit nomme 'gluten free' mais contenant d'autres allergenes : verifie qu'on se fie au texte, pas au nom",
        "texte": (
            "Farine d'amande, farine de lin doré, farine de graines de citrouille, "
            "poudre de blanc d'oeuf, agent de cuisson: bicarbonate de sodium, "
            "antioxydant: acide ascorbique (vitamine C), sel cristallisé rose."
        ),
        "allergenes_attendus": ["Fruits a coque", "Oeufs"],
    },
    {
        "id": "jus_de_fruit_multilingue_negatif",
        "description": "Cas negatif propre, texte quadrilingue (verifie l'absence de faux positifs sur un volume de texte important)",
        "texte": (
            "FRUIT JUICE FROM CONCENTRATE (APPLE, ORANGE 37%, STRAWBERRY 10%, CHERRY, "
            "WHITE GRAPE, PEAR)/ ZUTATEN: MEHRFRUCHTSAFT AUS FRUCHTSAFTKONZENTRATEN "
            "(APFEL, ORANGE 37%, ERDBEERE 10%, KIRSCH, WEISSE TRAUBE)/ INGRÉDIENTS: "
            "JUS DE FRUITS À BASE DE CONCENTRÉ (POMME, ORANGE 37%, FRAISE 10%, CERISE, "
            "RAISIN BLANC, POIRE)/ INGREDIENTEN: VRUCHTENSAP UIT CONCENTRAAT "
            "(APPEL, SINAASAPPEL 37%, AARDBEI 10%, KERS, WITTE DRUIF, PEER)"
        ),
        "allergenes_attendus": [],
    },
    {
        "id": "pain_de_campagne",
        "description": "Plusieurs synonymes du meme allergene dans un seul texte (ble, seigle, gluten, orge)",
        "texte": "water, unbleached unbromated enriched flour, rye flour, whole wheat flour, beer-dark, salt, wheat gluten, barley",
        "allergenes_attendus": ["Gluten (cereales)"],
    },
    {
        "id": "jus_orange_fraise_negatif",
        "description": "Cas negatif propre, texte tres court",
        "texte": "70% jus d'orange, 30% purée de fraise.",
        "allergenes_attendus": [],
    },
    {
        "id": "chocolat_precision_soja",
        "description": "Contient de la lecithine de TOURNESOL (pas de soja) : verifie l'absence de faux positif 'Soja'",
        "texte": "Sucre, cacao en pâte, beurre de cacao, émulsifiant: lécithine de tournesol, arôme naturel.",
        "allergenes_attendus": [],
    },
    {
        "id": "recette_quiche_lorraine",
        "description": (
            "Recette (pas un produit) avec plusieurs allergenes attendus. Limite assumee : "
            "l'ingredient 'pâte brisée (recette)' renvoie vers une sous-recette non deployee "
            "dans ce texte, donc le gluten qu'elle contient reellement n'est pas extractible "
            "de cette liste d'ingredients seule - non compte dans les attendus, documente "
            "comme limite architecturale plutot que comme echec du modele (voir "
            "docs/03-bloc2-ia/tests-modele.md)."
        ),
        "texte": (
            "1 pâte brisée (recette) ou pâte feuilletée (recette)\n"
            "200 grammes de lard fumé coupé en tout petits dés\n"
            "1/2 litre de crème fraîche, 10 cl de crème maigre\n"
            "4 œufs\n"
            "sel, poivre, noix de muscade."
        ),
        "allergenes_attendus": ["Lait", "Oeufs"],
    },
    {
        "id": "recette_ratatouille_negatif",
        "description": "Recette reelle sans aucun allergene du referentiel",
        "texte": (
            "3 aubergines\n2 courgettes\n2 poivrons\n400 g de tomates\n2 gousses d'ail\n"
            "3 oignons blancs\n2 cl d'huile d'olive à chaque cuisson de légume\n"
            "sel, laurier, thym, romarin."
        ),
        "allergenes_attendus": [],
    },
]
