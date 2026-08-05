-- Schema PostgreSQL de NutriScan IA (Bloc 1, competence C4).
-- Traduction directe du MLD documente dans docs/01-cadrage/merise.md.
-- Rejouable sans erreur (CREATE ... IF NOT EXISTS / ON CONFLICT DO NOTHING).

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ---------------------------------------------------------------------------
-- UTILISATEUR
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS utilisateur (
    id_utilisateur          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email                   TEXT NOT NULL UNIQUE,
    mot_de_passe_hash       TEXT NOT NULL,
    date_inscription        TIMESTAMPTZ NOT NULL DEFAULT now(),
    consentement_rgpd       BOOLEAN NOT NULL DEFAULT false,
    consentement_donnee_sante BOOLEAN NOT NULL DEFAULT false,
    date_suppression_demandee DATE
);

-- ---------------------------------------------------------------------------
-- ALLERGENE : referentiel officiel (reglement UE INCO 1169/2011, annexe II)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS allergene (
    id_allergene            SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    libelle                 TEXT NOT NULL UNIQUE,
    reference_reglementaire TEXT NOT NULL DEFAULT 'Reglement UE 1169/2011, annexe II'
);

INSERT INTO allergene (libelle) VALUES
    ('Gluten (cereales)'),
    ('Crustaces'),
    ('Oeufs'),
    ('Poissons'),
    ('Arachides'),
    ('Soja'),
    ('Lait'),
    ('Fruits a coque'),
    ('Celeri'),
    ('Moutarde'),
    ('Graines de sesame'),
    ('Anhydride sulfureux et sulfites'),
    ('Lupin'),
    ('Mollusques')
ON CONFLICT (libelle) DO NOTHING;

-- ---------------------------------------------------------------------------
-- UTILISATEUR_ALLERGENE : profil allergene/intolerance/preference.
-- Donnee de sante (RGPD art. 9) : le niveau est chiffre symetriquement avec
-- pgcrypto (pgp_sym_encrypt/pgp_sym_decrypt) ; la cle est fournie par
-- l'application via une variable d'environnement (RGPD_ENCRYPTION_KEY), elle
-- n'est jamais stockee en base. Un CHECK SQL classique sur les valeurs
-- autorisees ('allergie'/'intolerance'/'preference') n'est donc pas possible
-- sur la colonne chiffree : cette validation est faite cote application.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS utilisateur_allergene (
    id_utilisateur  BIGINT NOT NULL REFERENCES utilisateur(id_utilisateur) ON DELETE CASCADE,
    id_allergene    SMALLINT NOT NULL REFERENCES allergene(id_allergene) ON DELETE RESTRICT,
    niveau_chiffre  BYTEA NOT NULL,
    PRIMARY KEY (id_utilisateur, id_allergene)
);

-- ---------------------------------------------------------------------------
-- PRODUIT (Open Food Facts) et son association aux allergenes
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS produit (
    code_barres     TEXT PRIMARY KEY,
    nom             TEXT NOT NULL,
    marque          TEXT,
    categorie       TEXT,
    nutri_score     CHAR(1) CHECK (nutri_score IN ('a', 'b', 'c', 'd', 'e')),
    ingredients_texte TEXT NOT NULL,
    date_import     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_produit_categorie ON produit (categorie);

CREATE TABLE IF NOT EXISTS produit_allergene (
    code_barres     TEXT NOT NULL REFERENCES produit(code_barres) ON DELETE CASCADE,
    id_allergene    SMALLINT NOT NULL REFERENCES allergene(id_allergene) ON DELETE RESTRICT,
    PRIMARY KEY (code_barres, id_allergene)
);

-- ---------------------------------------------------------------------------
-- COMPOSITION_NUTRITIONNELLE (Ciqual) et INGREDIENT
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS composition_nutritionnelle (
    code_ciqual     TEXT PRIMARY KEY,
    libelle_aliment TEXT NOT NULL,
    energie_kcal    REAL,
    proteines_g     REAL,
    glucides_g      REAL,
    lipides_g       REAL
);

CREATE TABLE IF NOT EXISTS ingredient (
    id_ingredient   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    libelle         TEXT NOT NULL UNIQUE,
    code_ciqual     TEXT REFERENCES composition_nutritionnelle(code_ciqual) ON DELETE SET NULL
);

-- ---------------------------------------------------------------------------
-- RECETTE (scraping) et sa composition en ingredients
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS recette (
    id_recette      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    titre           TEXT NOT NULL,
    source_url      TEXT NOT NULL UNIQUE,
    instructions    TEXT,
    date_scraping   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS recette_ingredient (
    id_recette      BIGINT NOT NULL REFERENCES recette(id_recette) ON DELETE CASCADE,
    id_ingredient   BIGINT NOT NULL REFERENCES ingredient(id_ingredient) ON DELETE RESTRICT,
    quantite        TEXT,
    PRIMARY KEY (id_recette, id_ingredient)
);

-- ---------------------------------------------------------------------------
-- ANALYSE_COMPATIBILITE : resultat d'une analyse de compatibilite (Bloc 2,
-- historique US7), portant sur un produit OU une recette, jamais les deux
-- (cf. merise.md #3). Nommee ainsi (et non "analyse") car ANALYSE/ANALYZE
-- est un mot reserve du langage SQL de PostgreSQL (cf. VACUUM ANALYSE) : un
-- nom de table non-prefixe aurait provoque une erreur de syntaxe.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analyse_compatibilite (
    id_analyse              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_utilisateur          BIGINT NOT NULL REFERENCES utilisateur(id_utilisateur) ON DELETE CASCADE,
    code_barres             TEXT REFERENCES produit(code_barres) ON DELETE SET NULL,
    id_recette              BIGINT REFERENCES recette(id_recette) ON DELETE SET NULL,
    statut_compatibilite    TEXT NOT NULL CHECK (statut_compatibilite IN ('compatible', 'a_risque', 'incompatible')),
    allergenes_detectes     TEXT,
    substitutions_proposees TEXT,
    date_analyse            TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_analyse_produit_ou_recette CHECK (num_nonnulls(code_barres, id_recette) = 1)
);

CREATE INDEX IF NOT EXISTS idx_analyse_utilisateur ON analyse_compatibilite (id_utilisateur, date_analyse DESC);

-- ---------------------------------------------------------------------------
-- TRAITEMENT_RGPD : journal des traitements de donnees personnelles
-- (alimente le registre des traitements, voir docs/rgpd/registre-traitements.md)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS traitement_rgpd (
    id_traitement           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_utilisateur          BIGINT NOT NULL REFERENCES utilisateur(id_utilisateur) ON DELETE CASCADE,
    type_traitement         TEXT NOT NULL,
    finalite                TEXT NOT NULL,
    categorie_donnee_sante  BOOLEAN NOT NULL DEFAULT false,
    date_traitement         TIMESTAMPTZ NOT NULL DEFAULT now()
);
