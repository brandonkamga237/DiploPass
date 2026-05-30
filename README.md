# DigiPass — Suivi numérique de la diplomation

Plateforme web de gestion administrative des finissants de l'ENSET de Douala.  
Développée avec Flask 3.1 + PostgreSQL 16 + MinIO + Bootstrap 5.3, déployable via Docker.

---

## Table des matières

1. [Présentation](#1-présentation)
2. [Architecture technique](#2-architecture-technique)
3. [Structure du projet](#3-structure-du-projet)
4. [Prérequis](#4-prérequis)
5. [Installation et démarrage](#5-installation-et-démarrage)
6. [Identifiants de test](#6-identifiants-de-test)
7. [Rôles et fonctionnalités](#7-rôles-et-fonctionnalités)
8. [Workflow de diplomation](#8-workflow-de-diplomation)
9. [Modèle de données](#9-modèle-de-données)
10. [Routes de l'application](#10-routes-de-lapplication)
11. [Format d'import JSON](#11-format-dimport-json)
12. [Variables d'environnement](#12-variables-denvironnement)
13. [Docker — commandes utiles](#13-docker--commandes-utiles)
14. [Dépannage](#14-dépannage)

---

## 1. Présentation

DigiPass dématérialise le suivi du processus de diplomation à l'ENSET de Douala.  
Chaque finissant dispose d'un dossier numérique qui progresse à travers 14 statuts validés par les différents acteurs administratifs.

**Fonctionnalités principales :**
- Soumission en ligne du dossier de diplomation avec dépôt de fichiers (PDF/JPG/PNG)
- Stockage sécurisé des pièces justificatives sur MinIO (compatible S3)
- Gestion multi-rôles avec tableaux de bord adaptés (6 rôles)
- Transitions de statut avec historique horodaté complet
- Contrôle d'accès par année académique (session globale)
- Lancement du processus de diplomation par le Directeur via l'année académique
- Communiqués officiels publiés par le Directeur
- Import en masse des étudiants via fichier JSON
- URLs signées MinIO (1 800 s) pour la consultation sécurisée des documents

---

## 2. Architecture technique

| Couche | Technologie |
|--------|-------------|
| Backend | Python 3.13 / Flask 3.1 |
| ORM | SQLAlchemy 2.0 + Flask-SQLAlchemy 3.1 |
| Migrations | Flask-Migrate 4.0 (Alembic) |
| Base de données | PostgreSQL 16 (Docker) |
| Stockage fichiers | MinIO (compatible S3) — SDK `minio==7.2.15` |
| Authentification | Flask-Login 0.6 (multi-modèles) |
| Templates | Jinja2 3.1 |
| CSS/UI | Bootstrap 5.3.3 + Bootstrap Icons 1.11 (servis localement) |
| PDF | WeasyPrint 62 + Pillow 10 |
| WSGI (prod) | Gunicorn 22 |
| Conteneurisation | Docker Compose |

**Choix de conception :**
- Application Factory (`create_app`) pour l'isolation des contextes
- Blueprints séparés par rôle (`auth`, `etudiant`, `representant`, `chef_bureau`, `chef_service`, `directeur`, `admin`)
- Préfixe d'identité Flask-Login (`etudiant:XXX`, `representant:XXX`, etc.) pour la cohabitation multi-modèles
- Tous les assets Bootstrap/Icons servis localement — pas de CDN
- Police système (`-apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui`) — pas de Google Fonts
- `session['annee_active_code']` : contexte d'année académique global partagé entre rôles

---

## 3. Structure du projet

```
DigiPass/
├── app/
│   ├── __init__.py                  # Application factory (create_app)
│   ├── models/
│   │   ├── etudiant.py              # Etudiant (matricule PK, Flask-Login)
│   │   ├── representant.py          # RepresentantFiliere (Flask-Login)
│   │   ├── directeur.py             # Directeur (Flask-Login)
│   │   ├── chef_service.py          # ChefServiceScolarite (Flask-Login)
│   │   ├── chef_bureau.py           # ChefBureauDiplomation (Flask-Login)
│   │   ├── admin.py                 # Admin (Flask-Login)
│   │   ├── dossier_diplomation.py   # Dossier avec 14 statuts
│   │   ├── piece_jointe.py          # Fichiers uploadés (clé MinIO)
│   │   ├── dossier_formalisation.py # Checklist de clôture
│   │   ├── dossier_integration.py
│   │   ├── historique_phases.py     # Journal horodaté des transitions
│   │   ├── document_requis.py       # 16 documents requis (grille ENSET)
│   │   ├── communique.py            # Communiqués du directeur
│   │   ├── annee_diplomation.py     # Années académiques + processus
│   │   ├── filiere.py
│   │   └── promotion.py
│   ├── controllers/
│   │   ├── auth.py
│   │   ├── etudiant.py
│   │   ├── representant.py
│   │   ├── chef_bureau.py
│   │   ├── chef_service.py
│   │   ├── directeur.py
│   │   └── admin.py
│   ├── services/
│   │   ├── storage_service.py       # Abstraction MinIO (upload, URL signée, delete)
│   │   ├── import_service.py        # Import JSON des étudiants
│   │   ├── notification_service.py
│   │   └── pdf_service.py
│   ├── utils/
│   │   └── decorators.py            # @role_required
│   ├── templates/
│   │   ├── base.html                # Layout sidebar responsive
│   │   ├── auth/login.html
│   │   ├── etudiant/
│   │   ├── representant/
│   │   ├── chef_bureau/
│   │   ├── chef_service/
│   │   ├── directeur/
│   │   └── admin/
│   └── static/
│       ├── css/custom.css           # Design system (variables CSS, composants)
│       └── vendor/                  # Bootstrap, Icons (local — pas de CDN)
├── migrations/                      # Fichiers Alembic (générés)
├── init_db/
│   ├── create_tables.sql
│   └── seed_documents.sql           # 16 documents requis par défaut
├── seed.py                          # Script de peuplement de la base de test
├── config.py
├── run.py                           # Point d'entrée Flask
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## 4. Prérequis

**Développement local :**
- Python 3.11+
- Docker 24+ et Docker Compose 2.x (pour PostgreSQL et MinIO)
- pip

**Déploiement complet :**
- Docker 24+ et Docker Compose 2.x

---

## 5. Installation et démarrage

### Développement local (recommandé)

```bash
# 1. Cloner le dépôt
git clone https://github.com/votre-org/DigiPass.git
cd DigiPass

# 2. Créer l'environnement virtuel
python3 -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer l'environnement
cp .env.example .env
# Éditer .env — voir section Variables d'environnement ci-dessous
# Pour du local : DATABASE_URL doit pointer sur localhost, pas sur "db"

# 5. Démarrer PostgreSQL et MinIO via Docker
docker compose up -d db minio

# 6. Appliquer les migrations
flask db upgrade

# 7. Créer le bucket MinIO
python - <<'EOF'
from app import create_app
app = create_app()
with app.app_context():
    from app.services.storage_service import _client, BUCKET
    c = _client()
    if not c.bucket_exists(BUCKET):
        c.make_bucket(BUCKET)
        print("Bucket créé :", BUCKET)
EOF

# 8. Peupler la base avec les données de test
python seed.py

# 9. Lancer le serveur
flask run
# Accès : http://127.0.0.1:5000
```

### Déploiement Docker complet

```bash
# 1. Cloner et configurer
git clone https://github.com/votre-org/DigiPass.git
cd DigiPass
cp .env.example .env
# Éditer .env avec des valeurs de production sécurisées

# 2. Lancer tous les services
docker compose up --build -d
# Services : web (5000), db (5432), pgAdmin (5050), MinIO API (9000), MinIO Console (9001)

# 3. Appliquer les migrations
docker compose exec web flask db upgrade

# 4. Peupler la base
docker compose exec web python seed.py
```

---

## 6. Identifiants de test

> Tous ces comptes sont créés par `python seed.py`.  
> **Ne pas utiliser en production.**

### Personnel administratif

| Rôle | Nom | Login | Mot de passe |
|------|-----|-------|--------------|
| Admin système | — | `admin` | `admin1234` |
| Directeur de l'ENSET | FOUDA Jean-Pierre | `jean.fouda` | `enset2025` |
| Chef Service Scolarité | ELLA Brigitte-Marie | `brigitte.ella` | `enset2025` |
| Chef Bureau Diplomation | BELLO Samuel | `samuel.bello` | `enset2025` |

### Représentants de filière

| Filière | Nom | Login | Mot de passe |
|---------|-----|-------|--------------|
| GI | NKOA Rodrigue | `rodrigue.nkoa` | `enset2025` |
| GE | FEUSSI Patrick | `patrick.feussi` | `enset2025` |
| GC | ONDOA Guy | `guy.ondoa` | `enset2025` |
| GM | TCHAMBA Josue | `josue.tchamba` | `enset2025` |
| MAT | FOSSI Armand | `armand.fossi` | `enset2025` |
| PHY | TALLA André | `andre.talla` | `enset2025` |
| SI | WAFFO Lionel | `lionel.waffo` | `enset2025` |
| STI | YOUMBI Franck | `franck.youmbi` | `enset2025` |
| SPC | KENFACK Steve | `steve.kenfack` | `enset2025` |
| EEA | NGUEFACK Ulrich | `ulrich.nguefack` | `enset2025` |

### Étudiants (100 comptes — 10 par filière)

| Filière | Matricules | Mot de passe |
|---------|-----------|--------------|
| GI | `25GI001` … `25GI010` | = matricule |
| GE | `25GE001` … `25GE010` | = matricule |
| GC | `25GC001` … `25GC010` | = matricule |
| GM | `25GM001` … `25GM010` | = matricule |
| MAT | `25MAT001` … `25MAT010` | = matricule |
| PHY | `25PHY001` … `25PHY010` | = matricule |
| SI | `25SI001` … `25SI010` | = matricule |
| STI | `25STI001` … `25STI010` | = matricule |
| SPC | `25SPC001` … `25SPC010` | = matricule |
| EEA | `25EEA001` … `25EEA010` | = matricule |

> Tous les étudiants sont au statut **DEPOSE** sans aucun fichier joint — les vraies pièces doivent être déposées via l'interface.

### Console MinIO

| Champ | Valeur |
|-------|--------|
| URL | http://localhost:9001 |
| Login | `digipass` |
| Mot de passe | `digipass2026` |

### Interface pgAdmin

| Champ | Valeur |
|-------|--------|
| URL | http://localhost:5050 |
| Email | `admin@digipass.cm` |
| Mot de passe | `admin_password` |
| Hôte serveur PostgreSQL | `db` |
| Base | `digipass_db` |
| Utilisateur DB | `digipass_user` |

---

## 7. Rôles et fonctionnalités

### Étudiant
- Tableau de bord avec stepper de progression (11 étapes visuelles)
- Soumettre son dossier de diplomation en ligne avec dépôt de fichiers (PDF/JPG/PNG, max 10 Mo)
- Consulter, remplacer ou supprimer ses pièces justificatives depuis le détail du dossier
- Visualiser les fichiers déposés via URL signée MinIO
- Modifier son profil et changer son mot de passe

### Représentant de filière
- Tableau de bord avec donut d'avancement par filière
- Lister et filtrer les dossiers par statut
- Vérifier les dossiers (complet → `EN_VERIFICATION` / incomplet → `INCOMPLET`)
- Corriger les informations qui figureront sur le diplôme (nom, prénom, date/lieu de naissance)
- Confirmer l'étudiant sur la liste des finissants (`LISTE_FINISSANTS`)
- Gérer la formalisation (`FORMALISATION`) et clôturer les dossiers (`CLOTURE`)
- Consulter les pièces justificatives des étudiants

### Chef Bureau Diplomation
- Tableau de bord global avec pipeline de phases et indicateurs
- Authentifier les dossiers (`AUTHENTIFICATION` → `IMPRESSION_PROVISOIRE`)
- Lancer l'impression provisoire et la production définitive
- Transmettre les dossiers pour signature du Directeur (`SIGNATURE_DIRECTEUR`)

### Chef Service Scolarité
- Vue d'ensemble de tous les dossiers toutes filières confondues
- Faire passer les dossiers en signature Recteur (`SIGNATURE_RECTEUR`) et Ministre (`SIGNATURE_MINISTRE`)

### Directeur de l'ENSET
- Créer et gérer les années académiques (`AnneeDiplomation`)
- Lancer officiellement le processus de diplomation pour une année
- Publier des communiqués officiels de diplomation
- Signer les dossiers en attente (`SIGNATURE_DIRECTEUR`)

### Administrateur
- Créer les comptes de tout le personnel (Directeur, Chef Service, Représentants)
- Nommer/retirer le rôle de Chef Bureau à un représentant
- Activer/désactiver les comptes, réinitialiser les mots de passe
- Importer les étudiants en masse via fichier JSON
- Gérer les filières
- Consulter et modifier la liste des étudiants

---

## 8. Workflow de diplomation

Les dossiers progressent à travers les statuts suivants :

| # | Statut | Libellé | Acteur |
|---|--------|---------|--------|
| 1 | `DEPOSE` | Déposé | Étudiant |
| 2 | `EN_VERIFICATION` | En vérification | Représentant |
| 3 | `INCOMPLET` | Incomplet | Représentant → Étudiant |
| 4 | `AUTHENTIFICATION` | Authentification | Chef Bureau |
| 5 | `AUTH_REJETEE` | Auth. rejetée | Chef Bureau |
| 6 | `LISTE_FINISSANTS` | Liste finissants | Représentant |
| 7 | `IMPRESSION_PROVISOIRE` | Impression provisoire | Chef Bureau |
| 8 | `PRODUCTION_DEFINITIVE` | Production définitive | Chef Bureau |
| 9 | `SIGNATURE_DIRECTEUR` | Signature Directeur | Chef Bureau → Directeur |
| 10 | `SIGNATURE_RECTEUR` | Signature Recteur | Chef Service |
| 11 | `SIGNATURE_MINISTRE` | Signature Ministre | Chef Service |
| 12 | `FORMALISATION` | Formalisation | Représentant |
| 13 | `CLOTURE` | Clôturé | Représentant |
| 14 | `REJETE` | Rejeté | — |

```
DEPOSE
  └─ EN_VERIFICATION
       ├─ INCOMPLET ──────────────────► (retour à EN_VERIFICATION)
       └─ AUTHENTIFICATION
            ├─ AUTH_REJETEE
            └─ LISTE_FINISSANTS
                 └─ IMPRESSION_PROVISOIRE
                      └─ PRODUCTION_DEFINITIVE
                           └─ SIGNATURE_DIRECTEUR
                                └─ SIGNATURE_RECTEUR
                                     └─ SIGNATURE_MINISTRE
                                          └─ FORMALISATION
                                               └─ CLOTURE
```

Chaque transition est enregistrée dans `historique_phases` avec horodatage, identité et rôle de l'acteur.

---

## 9. Modèle de données

### Tables principales

| Table | Clé primaire | Description |
|-------|-------------|-------------|
| `etudiant` | `matricule` (VARCHAR) | Finissants — identité complète |
| `representant_filiere` | `id_representant` (SERIAL) | Représentants par filière |
| `directeur` | `id_directeur` (SERIAL) | Directeur de l'ENSET |
| `chef_service_scolarite` | `id_chef_service` (SERIAL) | Chef Service Scolarité |
| `chef_bureau_diplomation` | `id_chef_bureau` (SERIAL) | Chef Bureau Diplomation |
| `admin` | `id_admin` (SERIAL) | Administrateur système |
| `dossier_diplomation` | `id_dossier` (SERIAL) | Un dossier par étudiant |
| `piece_jointe` | `id_piece` (SERIAL) | Fichiers MinIO liés à un dossier |
| `dossier_formalisation` | `id_formalisation` (SERIAL) | Checklist de clôture |
| `historique_phases` | `id_historique` (SERIAL) | Journal des transitions |
| `document_requis` | `id_document` (SERIAL) | 16 documents exigés par défaut |
| `communique` | `id_communique` (SERIAL) | Communiqués du directeur |
| `annee_diplomation` | `id` (SERIAL) | Années académiques + flags processus |

### Relations clés

```
etudiant (1) ──────────────── (0..1) dossier_diplomation
dossier_diplomation (1) ────── (N) piece_jointe
dossier_diplomation (1) ────── (N) historique_phases
dossier_diplomation (1) ────── (0..1) dossier_formalisation
document_requis (1) ─────────── (N) piece_jointe
representant_filiere (1) ────── (N) dossier_diplomation
communique (1) ──────────────── (N) dossier_diplomation
```

### Clé MinIO dans `piece_jointe`

```
dossiers/{id_dossier}/{id_document}/{uuid}_{nom_original}
```

---

## 10. Routes de l'application

### `auth`

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/` | Redirection vers login |
| GET/POST | `/login` | Authentification multi-rôles |
| GET | `/logout` | Déconnexion |
| GET | `/annee/<code>` | Changer l'année académique active (session) |

### `etudiant` — préfixe `/etudiant`

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/dashboard` | Tableau de bord + stepper de progression |
| GET/POST | `/soumettre-dossier` | Créer son dossier + dépôt initial de fichiers |
| GET | `/dossier` | Détail du dossier, liste et gestion des pièces |
| POST | `/dossier/pieces/<id_document>/upload` | Déposer / remplacer une pièce |
| POST | `/dossier/pieces/<id_piece>/supprimer` | Supprimer une pièce |
| GET | `/dossier/pieces/<id_piece>/voir` | URL signée MinIO (redirect) |
| GET | `/profil` | Profil de l'étudiant |
| GET/POST | `/changer-mot-de-passe` | Changer le mot de passe |

### `representant` — préfixe `/representant`

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/dashboard` | Stats filière + donut + actions prioritaires |
| GET | `/dossiers` | Liste filtrée par statut |
| GET | `/dossiers/<id>` | Détail complet d'un dossier |
| POST | `/dossiers/<id>/verifier` | Marquer complet ou incomplet |
| POST | `/dossiers/<id>/corriger` | Corriger les infos diplôme |
| POST | `/dossiers/<id>/confirmer-liste` | Confirmer sur liste finissants |
| GET/POST | `/dossiers/<id>/formalisation` | Checklist de formalisation |
| POST | `/dossiers/<id>/cloturer` | Clôturer le dossier |
| GET | `/dossiers/<id_dossier>/pieces/<id_piece>/voir` | Consulter une pièce (URL signée) |

### `chef_bureau` — préfixe `/chef-bureau`

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/dashboard` | Tableau de bord global avec pipeline |
| GET | `/authentification` | Dossiers en attente d'authentification |
| GET | `/impressions` | Dossiers en impression / production |
| POST | `/dossiers/<id>/authentifier` | Authentifier (ou rejeter) |
| POST | `/dossiers/<id>/impression-provisoire` | Lancer l'impression provisoire |
| POST | `/dossiers/<id>/production-definitive` | Passer en production définitive |
| POST | `/dossiers/<id>/envoyer-directeur` | Envoyer pour signature Directeur |

### `chef_service` — préfixe `/chef-service`

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/dashboard` | Vue d'ensemble globale |
| GET | `/dossiers` | Tous les dossiers |
| POST | `/dossiers/<id>/passer-signature-recteur` | Passer en signature Recteur |
| POST | `/dossiers/<id>/passer-signature-ministre` | Passer en signature Ministre |

### `directeur` — préfixe `/directeur`

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/dashboard` | Tableau de bord |
| GET | `/dossiers-a-signer` | Dossiers à signer |
| POST | `/dossiers/<id>/signer` | Signer un dossier |
| GET | `/communiques` | Liste des communiqués |
| GET/POST | `/communiques/nouveau` | Créer un communiqué |
| POST | `/communiques/<id>/publier` | Publier un communiqué |
| POST | `/annees/<id>/lancer-processus` | Lancer le processus de diplomation |

### `admin` — préfixe `/admin`

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/dashboard` | Tableau de bord admin |
| POST | `/creer-compte` | Créer un compte personnel |
| GET | `/comptes` | Gérer tous les comptes |
| POST | `/comptes/representant/<id>/toggle-actif` | Activer/désactiver représentant |
| POST | `/comptes/representant/<id>/modifier` | Modifier représentant |
| POST | `/comptes/representant/<id>/nommer-chef-bureau` | Nommer Chef Bureau |
| POST | `/comptes/representant/<id>/retirer-chef-bureau` | Retirer Chef Bureau |
| POST | `/comptes/directeur/<id>/toggle-actif` | Activer/désactiver directeur |
| POST | `/comptes/directeur/<id>/modifier` | Modifier directeur |
| POST | `/comptes/chef-service/<id>/toggle-actif` | Activer/désactiver chef service |
| POST | `/comptes/chef-service/<id>/modifier` | Modifier chef service |
| POST | `/comptes/<type>/<id>/reset-mdp` | Réinitialiser le mot de passe |
| GET | `/etudiants` | Liste des étudiants |
| POST | `/etudiants/creer` | Créer un étudiant |
| POST | `/etudiants/<matricule>/modifier` | Modifier un étudiant |
| GET/POST | `/importer-etudiants` | Import JSON en masse |
| GET | `/annees` | Liste des années académiques |
| GET/POST | `/annees/nouvelle` | Créer une année académique |
| POST | `/annees/<id>/supprimer` | Supprimer une année |
| GET | `/filieres` | Liste des filières |
| GET/POST | `/filieres/nouvelle` | Créer une filière |
| POST | `/filieres/<code>/toggle` | Activer/désactiver une filière |

---

## 11. Format d'import JSON

L'administrateur peut importer des étudiants en masse via `/admin/importer-etudiants` :

```json
[
  {
    "matricule":          "25GI001",
    "nom":                "KAMGA",
    "prenom":             "Paul",
    "date_naissance":     "2001-05-10",
    "lieu_naissance":     "Douala",
    "filiere":            "GI",
    "niveau":             3,
    "cycle":              "Licence",
    "type_etudiant":      "REGULIER",
    "statut_fonctionnaire": false,
    "email":              "paul.kamga@etudiant.enset.cm",
    "telephone":          "699000001",
    "sexe":               "M",
    "annee_academique":   "2024-2025"
  }
]
```

**Champs obligatoires :** `matricule`, `nom`, `prenom`, `filiere`  
**Mot de passe initial :** automatiquement mis à la valeur du `matricule`  
**Doublons :** les matricules déjà existants sont ignorés sans erreur

---

## 12. Variables d'environnement

Copier `.env.example` en `.env` et adapter :

| Variable | Exemple local | Description |
|----------|--------------|-------------|
| `SECRET_KEY` | `changez-moi` | Clé de signature Flask (sessions) |
| `FLASK_APP` | `run.py` | Point d'entrée Flask |
| `FLASK_ENV` | `development` | Environnement |
| `DATABASE_URL` | `postgresql://digipass_user:digipass2026@localhost:5432/digipass_db` | Local : `localhost` / Docker : `db` |
| `POSTGRES_DB` | `digipass_db` | Nom de la base |
| `POSTGRES_USER` | `digipass_user` | Utilisateur PostgreSQL |
| `POSTGRES_PASSWORD` | `digipass2026` | Mot de passe PostgreSQL |
| `MINIO_ENDPOINT` | `localhost:9000` | Local : `localhost` / Docker : `minio:9000` |
| `MINIO_ACCESS_KEY` | `digipass` | Identifiant MinIO |
| `MINIO_SECRET_KEY` | `digipass2026` | Mot de passe MinIO |
| `MINIO_BUCKET` | `digipass` | Nom du bucket |
| `MINIO_SECURE` | `false` | `true` en production avec TLS |
| `PGADMIN_EMAIL` | `admin@digipass.cm` | Email pgAdmin |
| `PGADMIN_PASSWORD` | `admin_password` | Mot de passe pgAdmin |

> **Production :** générer une `SECRET_KEY` robuste :  
> `python3 -c "import secrets; print(secrets.token_hex(32))"`

---

## 13. Docker — commandes utiles

### Services définis dans `docker-compose.yml`

| Service | Image | Ports | Description |
|---------|-------|-------|-------------|
| `db` | `postgres:16-alpine` | 5432 | Base de données PostgreSQL |
| `web` | Build local | 5000 | Application Flask / Gunicorn |
| `pgadmin` | `dpage/pgadmin4` | 5050 | Interface web PostgreSQL |
| `minio` | `minio/minio:latest` | 9000 (API), 9001 (Console) | Stockage objets S3 |

### Commandes courantes

```bash
# Démarrer tous les services
docker compose up -d

# Démarrer uniquement DB et MinIO (pour dev local)
docker compose up -d db minio

# Arrêter tous les services
docker compose down

# Reset complet (supprime tous les volumes)
docker compose down -v

# Logs en temps réel
docker compose logs -f web

# Shell dans le conteneur web
docker compose exec web bash

# Appliquer les migrations
docker compose exec web flask db upgrade

# Peupler la base
docker compose exec web python seed.py

# Shell PostgreSQL
docker compose exec db psql -U digipass_user -d digipass_db

# Rebuild après modification du code
docker compose up --build -d
```

---

## 14. Dépannage

### `Connection refused` sur port 9000 (MinIO)

MinIO n'est pas démarré.

```bash
docker compose up -d minio
# Vérifier :
docker ps --filter name=minio
```

Puis créer le bucket si nécessaire :

```bash
python - <<'EOF'
from app import create_app
app = create_app()
with app.app_context():
    from app.services.storage_service import _client, BUCKET
    c = _client()
    if not c.bucket_exists(BUCKET):
        c.make_bucket(BUCKET)
        print("Bucket créé")
    else:
        print("Bucket déjà existant")
EOF
```

### `could not translate host name "db"` (connexion DB)

En développement local, `DATABASE_URL` doit utiliser `localhost` et non `db` :

```
DATABASE_URL=postgresql://digipass_user:digipass2026@localhost:5432/digipass_db
```

### `AttributeError: 'DossierDiplomation' object has no attribute 'pieces_jointes'`

Le serveur Flask tourne avec une ancienne version du modèle en mémoire. Redémarrer Flask.

### `document_requis` vide (aucun document affiché)

Le fichier `seed_documents.sql` n'a pas été exécuté :

```bash
psql -h localhost -U digipass_user -d digipass_db -f init_db/seed_documents.sql
# Ou via Docker :
docker compose exec db psql -U digipass_user -d digipass_db \
  -f /docker-entrypoint-initdb.d/02_seed.sql
```

### Migrations en conflit (`Multiple head revisions`)

```bash
flask db merge heads -m "merge"
flask db upgrade
```

### Dashboard ne charge pas (302 en boucle)

Verrou PostgreSQL actif — libérer les connexions bloquées :

```sql
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'digipass_db'
  AND pid <> pg_backend_pid()
  AND state IN ('active', 'idle in transaction');
```

---

## Licence

Projet académique — ENSET de Douala, 2025-2026.  
Tous droits réservés.
