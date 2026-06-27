-- DiploPass — Schéma initial PostgreSQL
-- Ce fichier est exécuté automatiquement par Docker au premier démarrage.

CREATE TABLE IF NOT EXISTS admin (
    id_admin       SERIAL       PRIMARY KEY,
    nom            VARCHAR(100) NOT NULL,
    prenom         VARCHAR(100) NOT NULL DEFAULT '',
    login          VARCHAR(100) UNIQUE NOT NULL,
    mot_de_passe   VARCHAR(255) NOT NULL,
    actif          BOOLEAN      DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS etudiant (
    matricule              VARCHAR(20)  PRIMARY KEY,
    nom                    VARCHAR(100) NOT NULL,
    prenom                 VARCHAR(100) NOT NULL,
    date_naissance         DATE         NOT NULL,
    lieu_naissance         VARCHAR(150),
    filiere                VARCHAR(100) NOT NULL,
    niveau                 INTEGER,
    cycle                  VARCHAR(20)  CHECK (cycle IN ('LICENCE','MASTER')),
    type_etudiant          VARCHAR(20)  CHECK (type_etudiant IN ('REGULIER','AUDITEUR_LIBRE','FONCTIONNAIRE')),
    statut_fonctionnaire   BOOLEAN      DEFAULT FALSE,
    email                  VARCHAR(150) UNIQUE,
    telephone              VARCHAR(20),
    numero_cni             VARCHAR(50),
    promotion              VARCHAR(20),
    sexe                   CHAR(1)      CHECK (sexe IN ('M','F')),
    mot_de_passe           VARCHAR(255) NOT NULL,
    annee_academique       VARCHAR(9),
    actif                  BOOLEAN      DEFAULT TRUE,
    created_at             TIMESTAMP    DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS directeur (
    id_directeur   SERIAL       PRIMARY KEY,
    nom            VARCHAR(100) NOT NULL,
    prenom         VARCHAR(100) NOT NULL,
    grade          VARCHAR(100),
    login          VARCHAR(100) UNIQUE NOT NULL,
    mot_de_passe   VARCHAR(255) NOT NULL,
    actif          BOOLEAN      DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS chef_service_scolarite (
    id_chef_service SERIAL       PRIMARY KEY,
    nom             VARCHAR(100) NOT NULL,
    prenom          VARCHAR(100) NOT NULL,
    login           VARCHAR(100) UNIQUE NOT NULL,
    mot_de_passe    VARCHAR(255) NOT NULL,
    actif           BOOLEAN      DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS chef_bureau_diplomation (
    id_chef_bureau SERIAL       PRIMARY KEY,
    nom            VARCHAR(100) NOT NULL,
    prenom         VARCHAR(100) NOT NULL,
    login          VARCHAR(100) UNIQUE NOT NULL,
    mot_de_passe   VARCHAR(255) NOT NULL,
    actif          BOOLEAN      DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS departement (
    code  VARCHAR(20)  PRIMARY KEY,
    nom   VARCHAR(150) NOT NULL,
    actif BOOLEAN      DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS filiere (
    id_filiere       SERIAL       PRIMARY KEY,
    code             VARCHAR(20)  UNIQUE NOT NULL,
    nom              VARCHAR(150) NOT NULL,
    cycle            VARCHAR(30),
    actif            BOOLEAN      DEFAULT TRUE,
    code_departement VARCHAR(20)  REFERENCES departement(code)
);

CREATE TABLE IF NOT EXISTS representant_filiere (
    id_representant  SERIAL       PRIMARY KEY,
    nom              VARCHAR(100) NOT NULL,
    prenom           VARCHAR(100) NOT NULL,
    filiere_geree    VARCHAR(100) NOT NULL,
    code_filiere     VARCHAR(20)  REFERENCES filiere(code),
    code_departement VARCHAR(20)  REFERENCES departement(code),
    bureau           VARCHAR(100),
    login            VARCHAR(100) UNIQUE NOT NULL,
    mot_de_passe     VARCHAR(255) NOT NULL,
    est_chef_bureau  BOOLEAN      DEFAULT FALSE NOT NULL,
    actif            BOOLEAN      DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS communique (
    id_communique      SERIAL       PRIMARY KEY,
    numero_communique  VARCHAR(50)  UNIQUE NOT NULL,
    titre              VARCHAR(255) NOT NULL,
    contenu            TEXT,
    date_emission      DATE         NOT NULL,
    date_limite_depot  DATE,
    annee_academique   VARCHAR(9)   NOT NULL,
    objet              VARCHAR(255),
    type_processus     VARCHAR(20)  CHECK (type_processus IN ('DIPLOMATION','INTEGRATION')),
    statut             VARCHAR(20)  CHECK (statut IN ('BROUILLON','PUBLIE')) DEFAULT 'BROUILLON',
    promotion_cible    VARCHAR(100),
    id_directeur       INTEGER      REFERENCES directeur(id_directeur),
    created_at         TIMESTAMP    DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dossier_diplomation (
    id_dossier                    SERIAL      PRIMARY KEY,
    matricule                     VARCHAR(20) NOT NULL REFERENCES etudiant(matricule),
    date_depot                    TIMESTAMP   DEFAULT NOW(),
    statut                        VARCHAR(30) NOT NULL DEFAULT 'DEPOSE'
        CHECK (statut IN (
            'DEPOSE','EN_VERIFICATION','INCOMPLET',
            'AUTHENTIFICATION','AUTH_REJETEE',
            'SOUMISSION_PHYSIQUE',
            'LISTE_FINISSANTS','IMPRESSION_PROVISOIRE',
            'PRODUCTION_DEFINITIVE','SIGNATURE_DIRECTEUR',
            'SIGNATURE_RECTEUR','SIGNATURE_MINISTRE',
            'FORMALISATION','CLOTURE','REJETE','NON_ELIGIBLE'
        )),
    montant_frais                 NUMERIC(10,2),
    frais_payes                   BOOLEAN     DEFAULT FALSE,
    date_soumission_physique      DATE,
    reference_recu                VARCHAR(50),
    resultat_authentification     VARCHAR(15) CHECK (resultat_authentification IN ('AUTHENTIQUE','FAUX')),
    nom_sur_diplome               VARCHAR(150),
    prenom_sur_diplome            VARCHAR(150),
    ddn_sur_diplome               DATE,
    lddn_sur_diplome              VARCHAR(150),
    statut_production_diplome     VARCHAR(30),
    date_signature_directeur      DATE,
    date_signature_recteur        DATE,
    date_signature_ministre       DATE,
    type_diplome                  VARCHAR(50),
    est_diplome_conforme          BOOLEAN,
    annee_academique              VARCHAR(9),
    observations                  TEXT,
    date_limite_depot             DATE,
    signature_empreinte_registre  BOOLEAN     DEFAULT FALSE,
    toge_remise                   BOOLEAN     DEFAULT FALSE,
    journal_promo_remis           BOOLEAN     DEFAULT FALSE,
    motif_rejet                   TEXT,
    id_communique                 INTEGER     REFERENCES communique(id_communique),
    id_representant               INTEGER     REFERENCES representant_filiere(id_representant),
    id_chef_bureau                INTEGER     REFERENCES chef_bureau_diplomation(id_chef_bureau),
    created_at                    TIMESTAMP   DEFAULT NOW(),
    updated_at                    TIMESTAMP   DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dossier_formalisation (
    id_formalisation              SERIAL      PRIMARY KEY,
    id_dossier                    INTEGER     UNIQUE NOT NULL REFERENCES dossier_diplomation(id_dossier),
    matricule                     VARCHAR(20) NOT NULL REFERENCES etudiant(matricule),
    date_constitution             TIMESTAMP   DEFAULT NOW(),
    statut                        VARCHAR(20) DEFAULT 'EN_ATTENTE'
        CHECK (statut IN ('EN_ATTENTE','INCOMPLET','VALIDE')),
    recu_quitus_cycle             BOOLEAN     DEFAULT FALSE,
    quitus_non_redevance          BOOLEAN     DEFAULT FALSE,
    attestation_depot_memoire     BOOLEAN     DEFAULT FALSE,
    recu_association_etudiants    BOOLEAN     DEFAULT FALSE,
    photocopie_cni                BOOLEAN     DEFAULT FALSE,
    photocopie_badge_etudiant     BOOLEAN     DEFAULT FALSE,
    quitus_bibliotheque           BOOLEAN     DEFAULT FALSE,
    date_signature_registre       TIMESTAMP,
    annee_academique              VARCHAR(9)
);

CREATE TABLE IF NOT EXISTS dossier_integration (
    id_dossier_integration          SERIAL      PRIMARY KEY,
    matricule                       VARCHAR(20) NOT NULL REFERENCES etudiant(matricule),
    date_depot                      TIMESTAMP   DEFAULT NOW(),
    statut                          VARCHAR(30) DEFAULT 'EN_CONSTITUTION'
        CHECK (statut IN ('EN_CONSTITUTION','TRANSMIS_MINFOPRA','INCOMPLET_MINFOPRA','AFFECTE','CLOTURE')),
    frais_visite_medicale           BOOLEAN     DEFAULT FALSE,
    photocopie_cni                  BOOLEAN     DEFAULT FALSE,
    photocopie_acte_naissance       BOOLEAN     DEFAULT FALSE,
    photocopie_dipet                BOOLEAN     DEFAULT FALSE,
    demi_cartes_photos              BOOLEAN     DEFAULT FALSE,
    dactylographie_attestation      BOOLEAN     DEFAULT FALSE,
    bordereau                       BOOLEAN     DEFAULT FALSE,
    signature_correspondance_dir    BOOLEAN     DEFAULT FALSE,
    observations                    TEXT,
    annee_academique                VARCHAR(9),
    lieu_affectation                VARCHAR(200),
    date_prise_service              DATE,
    heure_prise_service             TIME,
    date_transmission_minfopra      DATE,
    date_limite_depot               DATE,
    id_representant                 INTEGER     REFERENCES representant_filiere(id_representant),
    id_chef_bureau                  INTEGER     REFERENCES chef_bureau_diplomation(id_chef_bureau)
);

CREATE TABLE IF NOT EXISTS document_requis (
    id_document      SERIAL       PRIMARY KEY,
    numero           VARCHAR(5)   NOT NULL,
    nom              VARCHAR(500) NOT NULL,
    observation      VARCHAR(300),
    obligatoire      BOOLEAN      DEFAULT TRUE,
    conditionnel     BOOLEAN      DEFAULT FALSE,
    condition_texte  VARCHAR(300)
);

CREATE TABLE IF NOT EXISTS historique_phases (
    id_historique  SERIAL      PRIMARY KEY,
    id_dossier     INTEGER     NOT NULL REFERENCES dossier_diplomation(id_dossier),
    phase          VARCHAR(50) NOT NULL,
    ancien_statut  VARCHAR(30),
    nouveau_statut VARCHAR(30),
    commentaire    TEXT,
    id_acteur      VARCHAR(50),
    role_acteur    VARCHAR(50),
    date_action    TIMESTAMP   DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS annee_diplomation (
    id               SERIAL      PRIMARY KEY,
    code             VARCHAR(9)  UNIQUE NOT NULL,
    actif            BOOLEAN     DEFAULT TRUE,
    processus_lance  BOOLEAN     NOT NULL DEFAULT FALSE,
    liste_finalisee  BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at       TIMESTAMP   DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS piece_jointe (
    id_piece           SERIAL       PRIMARY KEY,
    id_dossier         INTEGER      NOT NULL REFERENCES dossier_diplomation(id_dossier) ON DELETE CASCADE,
    id_document_requis INTEGER      REFERENCES document_requis(id_document),
    nom_original       VARCHAR(255) NOT NULL,
    cle_minio          VARCHAR(500) NOT NULL UNIQUE,
    mime_type          VARCHAR(100),
    taille_octets      INTEGER,
    date_upload        TIMESTAMP    DEFAULT NOW(),
    statut             VARCHAR(20)  DEFAULT 'DEPOSE'
);

CREATE TABLE IF NOT EXISTS notification (
    id                  SERIAL       PRIMARY KEY,
    destinataire_type   VARCHAR(30)  NOT NULL,
    destinataire_id     INTEGER,
    filiere             VARCHAR(100),
    message             TEXT         NOT NULL,
    lue                 BOOLEAN      DEFAULT FALSE,
    type_notif          VARCHAR(20)  DEFAULT 'info',
    lien                VARCHAR(255),
    created_at          TIMESTAMP    DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS liste_finissants (
    id                  SERIAL       PRIMARY KEY,
    matricule           VARCHAR(20)  NOT NULL,
    nom                 VARCHAR(100) NOT NULL,
    prenom              VARCHAR(100) NOT NULL,
    date_naissance      DATE,
    lieu_naissance      VARCHAR(150),
    filiere             VARCHAR(20),
    cycle               VARCHAR(20),
    annee_academique    VARCHAR(9)   NOT NULL,
    valide              BOOLEAN      NOT NULL DEFAULT TRUE,
    motif_invalidation  TEXT,
    statut_correction   VARCHAR(20)  NOT NULL DEFAULT 'BROUILLON',
    created_at          TIMESTAMP    DEFAULT NOW(),
    updated_at          TIMESTAMP    DEFAULT NOW(),
    CONSTRAINT uq_finissant_annee UNIQUE (matricule, annee_academique)
);
