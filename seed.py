#!/usr/bin/env python3
"""
seed.py — Peuplement complet de la base DiploPass
==================================================

Comptes créés (mdp = enset2025 pour tout le monde sauf admin) :

  RÔLE                   NOM COMPLET                  LOGIN              MDP
  ─────────────────────────────────────────────────────────────────────────────
  Admin (existant)       Système Admin                admin              admin1234
  Directeur              FOUDA Jean-Pierre            jean.fouda         enset2025
  Chef Service Scolarité ELLA Brigitte-Marie          brigitte.ella      enset2025
  Chef Bureau Diplom.    BELLO Samuel                 samuel.bello       enset2025

  REPRÉSENTANTS DE DÉPARTEMENT (login = prenom.nom, mdp = enset2025)
  ─────────────────────────────────────────────────────────────────────────────
  GCI  Génie Civil                       ONDOA Guy              guy.ondoa
  GEL  Génie Électrique                  FEUSSI Patrick         patrick.feussi
  GME  Génie Mécanique                   TCHAMBA Josué          josue.tchamba
  STEG Sciences et Tech. Éco. & Gestion  MBALLA Roger           roger.mballa
  TAD  Techniques Administratives        NGONO Claire           claire.ngono
  ESF  Économie Sociale et Familiale     OWONA Sylvie           sylvie.owona
  ITH  Industrie Textile & Habillement   FOTSO Marc             marc.fotso
  GFO  Génie Forestier                   FOGUE André            andre.fogue
  GCH  Génie Chimique                    ESSAMA Paul            paul.essama
  GINFO Génie Informatique               NKOA Rodrigue          rodrigue.nkoa
  SED  Sciences de l'Éducation           TALLA André            andre.talla
  ESB  Enseignement Scientifique de Base FOSSI Armand           armand.fossi

  ÉTUDIANTS — 120 au total, 5 à 10 par filière
  Login = matricule (ex: 25BTP001)   MDP = matricule

Usage :
    python seed.py
"""

import datetime
import random

from app import create_app, db

ANNEE      = "2025-2026"
MDP_STAFF  = "enset2025"

# ─── Départements ─────────────────────────────────────────────────────────────
# (code, nom)
DEPARTEMENTS = [
    ("GCI",   "Génie Civil"),
    ("GEL",   "Génie Électrique"),
    ("GME",   "Génie Mécanique"),
    ("STEG",  "Sciences et Techniques Économiques et de Gestion"),
    ("TAD",   "Techniques Administratives"),
    ("ESF",   "Économie Sociale et Familiale"),
    ("ITH",   "Industrie Textile et de l'Habillement"),
    ("GFO",   "Génie Forestier"),
    ("GCH",   "Génie Chimique"),
    ("GINFO", "Génie Informatique"),
    ("SED",   "Sciences de l'Éducation"),
    ("ESB",   "Enseignement Scientifique de Base"),
]

# ─── Filières ─────────────────────────────────────────────────────────────────
# (code_filiere, nom_filiere, code_departement)
FILIERES = [
    # Génie Civil
    ("BTP",  "Bâtiment et Travaux Publics",                    "GCI"),
    ("GT",   "Géomètre Topographe",                            "GCI"),
    ("ISA",  "Installation Sanitaire et Assainissement",       "GCI"),
    # Génie Électrique
    ("EN",   "Électronique",                                   "GEL"),
    ("ET",   "Électrotechnique",                               "GEL"),
    ("FC",   "Froid et Climatisation",                         "GEL"),
    ("TE",   "Thermique et Énergie",                           "GEL"),
    # Génie Mécanique
    ("CM",   "Construction Mécanique",                         "GME"),
    ("FM",   "Fabrication Mécanique",                          "GME"),
    ("MA",   "Mécanique Automobile",                           "GME"),
    # Sciences et Techniques Éco. & Gestion
    ("CF",   "Comptabilité et Finance",                        "STEG"),
    ("ECO",  "Économie",                                       "STEG"),
    ("MKG",  "Marketing",                                      "STEG"),
    # Techniques Administratives
    ("CA",   "Communication Administrative",                   "TAD"),
    # Économie Sociale et Familiale
    ("ESF",  "Économie Sociale et Familiale",                  "ESF"),
    # Industrie Textile et Habillement
    ("ITH",  "Industrie Textiles et de l'Habillement",         "ITH"),
    # Génie Forestier
    ("STB",  "Sciences et Technologie du Bois",                "GFO"),
    # Génie Chimique
    ("GCH",  "Chimie Industrielle",                            "GCH"),
    # Génie Informatique
    ("II",   "Informatique Industriel",                        "GINFO"),
    ("TIC",  "Technologie de l'Information et de la Communication", "GINFO"),
    # Sciences de l'Éducation
    ("CO",   "Conseil d'Orientation",                          "SED"),
    # Enseignement Scientifique de Base
    ("IM",   "Ingénierie Mathématique",                        "ESB"),
]

# ─── Représentants de département ─────────────────────────────────────────────
# (code_dept, nom, prenom, login)
REPS = [
    ("GCI",   "ONDOA",    "Guy",      "guy.ondoa"),
    ("GEL",   "FEUSSI",   "Patrick",  "patrick.feussi"),
    ("GME",   "TCHAMBA",  "Josue",    "josue.tchamba"),
    ("STEG",  "MBALLA",   "Roger",    "roger.mballa"),
    ("TAD",   "NGONO",    "Claire",   "claire.ngono"),
    ("ESF",   "OWONA",    "Sylvie",   "sylvie.owona"),
    ("ITH",   "FOTSO",    "Marc",     "marc.fotso"),
    ("GFO",   "FOGUE",    "Andre",    "andre.fogue"),
    ("GCH",   "ESSAMA",   "Paul",     "paul.essama"),
    ("GINFO", "NKOA",     "Rodrigue", "rodrigue.nkoa"),
    ("SED",   "TALLA",    "Andre",    "andre.talla"),
    ("ESB",   "FOSSI",    "Armand",   "armand.fossi"),
]

# ─── Pool de noms camerounais ──────────────────────────────────────────────────
NOMS = [
    "MBALLA", "FOGUE", "ONDOA", "ESSAMA", "NGONO", "OWONA", "TABI",
    "NJOYA", "SIMO", "FOTSO", "DJOUMESSI", "TANKEU", "FEUSSI", "MBASSI",
    "FOSSI", "NZEUTE", "ELONG", "ATANGANA", "MBOUDA", "FEZEU", "TAKEM",
    "NGOUNOU", "MEKONTSO", "TALLA", "TOUKAM", "KAZE", "DZOSSA", "WAFFO",
    "KOUAM", "YOUMBI", "TCHINDA", "TAMKO", "NGANOU", "TIOFACK", "FEUDJIO",
    "KENMEUGNE", "DONFACK", "NKUISSI", "POUOGANG", "DJOMO", "GUIMFAC",
    "TCHOUANTE", "NKEMENI", "TASSEMBE", "MBOUWE", "NZOGANG", "PIAMBA",
    "KAPTUE", "YEMELE", "BATCHOU", "GHOMSI", "MVONDO", "ABOMO", "OLINGA",
    "BELINGA", "NTSAMA", "ETOUNDI", "AKONO", "MEBENGA", "OBAM", "ZANG",
]

PRENOMS_M = [
    "Jean-Baptiste", "Paul", "Emmanuel", "François", "Alain", "Christian",
    "Roger", "Claude", "Bertrand", "Samuel", "Armand", "Thierry", "Patrice",
    "Marc", "Henri", "Nicolas", "Lionel", "Ulrich", "Wilfried", "Loïc",
    "Stève", "Kevin", "Dylan", "Axel", "Bryan", "Fabrice", "Rodrigue",
    "Landry", "Gaston", "André",
]

PRENOMS_F = [
    "Marie", "Claire", "Hélène", "Solange", "Yvette", "Christelle",
    "Sandra", "Nadège", "Carine", "Sylvie", "Florence", "Agnès",
    "Jeanne", "Corinne", "Patricia", "Rachel", "Laure", "Nathalie",
    "Murielle", "Vanessa", "Laetitia", "Chancelle", "Ornella", "Grâce",
    "Audrey", "Joëlle", "Brigitte",
]

VILLES = [
    "Douala", "Yaoundé", "Bafoussam", "Bamenda", "Garoua", "Maroua",
    "Ngaoundéré", "Bertoua", "Ebolowa", "Kumba", "Edéa", "Kribi",
    "Dschang", "Foumban", "Limbe", "Nkongsamba", "Mbalmayo",
]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _ddn():
    return datetime.date(
        random.randint(1998, 2004),
        random.randint(1, 12),
        random.randint(1, 28),
    )

def _tel():
    prefix = random.choice(["6", "6", "6", "2"])
    digits = "".join(str(random.randint(0, 9)) for _ in range(7))
    return f"+237 {prefix}{digits[:2]} {digits[2:4]} {digits[4:6]} {digits[6:]}"

def _depot():
    start = datetime.datetime(2025, 9, 15)
    end   = datetime.datetime(2026, 2, 20)
    return start + datetime.timedelta(days=random.randint(0, (end - start).days))


# ─── Seed principal ───────────────────────────────────────────────────────────

def seed():
    app = create_app()
    with app.app_context():

        from app.models.departement         import Departement
        from app.models.filiere             import Filiere
        from app.models.directeur           import Directeur
        from app.models.chef_service        import ChefServiceScolarite
        from app.models.representant        import RepresentantFiliere
        from app.models.etudiant            import Etudiant
        from app.models.dossier_diplomation import DossierDiplomation
        from app.models.annee_diplomation   import AnneeDiplomation
        from app.models.communique          import Communique
        from app.models.historique_phases   import HistoriquePhases
        from app.models.dossier_formalisation import DossierFormalisation

        # ── 0. Purge (ordre FK) ───────────────────────────────────────────────
        print("→ Purge des données seed précédentes…")
        HistoriquePhases.query.delete()
        DossierFormalisation.query.delete()
        DossierDiplomation.query.delete()
        Communique.query.delete()
        Etudiant.query.delete()
        RepresentantFiliere.query.delete()
        ChefServiceScolarite.query.delete()
        Directeur.query.delete()
        Filiere.query.delete()
        Departement.query.delete()
        db.session.commit()
        print("  ✓ Tables purgées.")

        # ── 1. Année 2025-2026 ────────────────────────────────────────────────
        annee_obj = AnneeDiplomation.query.filter_by(code=ANNEE).first()
        if not annee_obj:
            annee_obj = AnneeDiplomation(code=ANNEE, actif=True, processus_lance=False)
            db.session.add(annee_obj)
            db.session.flush()
        print(f"  ✓ Année {ANNEE} OK.")

        # ── 2. Départements ───────────────────────────────────────────────────
        print("→ Insertion des départements…")
        for code, nom in DEPARTEMENTS:
            dept = Departement(code=code, nom=nom, actif=True)
            db.session.add(dept)
        db.session.flush()
        print(f"  ✓ {len(DEPARTEMENTS)} départements insérés.")

        # ── 3. Filières ───────────────────────────────────────────────────────
        print("→ Insertion des filières…")
        for code, nom, code_dept in FILIERES:
            fil = Filiere(code=code, nom=nom, code_departement=code_dept, actif=True)
            db.session.add(fil)
        db.session.flush()
        print(f"  ✓ {len(FILIERES)} filières insérées.")

        # ── 4. Directeur ──────────────────────────────────────────────────────
        directeur = Directeur(
            nom="FOUDA", prenom="Jean-Pierre",
            grade="Professeur des Universités",
            login="jean.fouda", actif=True,
        )
        directeur.set_password(MDP_STAFF)
        db.session.add(directeur)
        db.session.flush()
        print(f"  ✓ Directeur       → jean.fouda        / {MDP_STAFF}")

        # ── 5. Chef Service Scolarité ─────────────────────────────────────────
        chef_service = ChefServiceScolarite(
            nom="ELLA", prenom="Brigitte-Marie",
            login="brigitte.ella", actif=True,
        )
        chef_service.set_password(MDP_STAFF)
        db.session.add(chef_service)
        db.session.flush()
        print(f"  ✓ Chef Service    → brigitte.ella     / {MDP_STAFF}")

        # ── 6. Chef Bureau Diplomation ────────────────────────────────────────
        chef_bureau = RepresentantFiliere(
            nom="BELLO", prenom="Samuel",
            login="samuel.bello",
            filiere_geree="GINFO",
            code_departement="GINFO",
            bureau="Bureau de la Diplomation",
            est_chef_bureau=True, actif=True,
        )
        chef_bureau.set_password(MDP_STAFF)
        db.session.add(chef_bureau)
        db.session.flush()
        print(f"  ✓ Chef Bureau     → samuel.bello      / {MDP_STAFF}")

        # ── 7. Représentants de département ──────────────────────────────────
        PRENOMS_AFFICHES = {
            "josue.tchamba": "Josué",
            "andre.fogue":   "André",
            "andre.talla":   "André",
        }
        representants = {}
        for code_dept, nom, prenom, login in REPS:
            prenom_affiche = PRENOMS_AFFICHES.get(login, prenom)
            rep = RepresentantFiliere(
                nom=nom, prenom=prenom_affiche, login=login,
                filiere_geree=code_dept,
                code_departement=code_dept,
                est_chef_bureau=False, actif=True,
            )
            rep.set_password(MDP_STAFF)
            db.session.add(rep)
            db.session.flush()
            representants[code_dept] = rep
            print(f"  ✓ Rep {code_dept:<6}      → {login:<22} / {MDP_STAFF}")

        # ── 8. Processus + communiqué ─────────────────────────────────────────
        annee_obj.processus_lance = True
        communique = Communique(
            numero_communique="COMM-2025-001",
            titre="Ouverture du processus de diplomation — Promotion 2025-2026",
            contenu=(
                "Les étudiants finissants de la promotion 2025-2026 sont invités à constituer "
                "et déposer leur dossier de diplomation via la plateforme DiploPass avant le "
                "28 février 2026. Chaque dossier doit inclure toutes les pièces requises. "
                "Tout dossier incomplet sera retourné à l'étudiant pour correction."
            ),
            date_emission=datetime.date(2025, 9, 15),
            date_limite_depot=datetime.date(2026, 2, 28),
            annee_academique=ANNEE,
            objet="Diplomation 2025-2026 — Appel à dépôt de dossiers",
            type_processus="DIPLOMATION",
            statut="PUBLIE",
            id_directeur=directeur.id_directeur,
        )
        db.session.add(communique)
        db.session.flush()
        print(f"  ✓ Communiqué publié → COMM-2025-001")

        # ── 9. Étudiants (5 par filière) ──────────────────────────────────────
        print("→ Génération des étudiants…")
        noms_utilises   = set()
        emails_utilises = set()

        for code_fil, _, code_dept in FILIERES:
            rep = representants[code_dept]
            for i in range(1, 6):
                sexe   = random.choices(["M", "F"], weights=[72, 28])[0]
                prenom = random.choice(PRENOMS_M if sexe == "M" else PRENOMS_F)
                for _ in range(30):
                    nom = random.choice(NOMS)
                    if (nom, prenom) not in noms_utilises:
                        break
                noms_utilises.add((nom, prenom))

                matricule = f"25{code_fil}{i:03d}"
                cycle     = random.choices(["LICENCE", "MASTER"], weights=[65, 35])[0]
                niveau    = 3 if cycle == "LICENCE" else 2

                base  = f"{prenom.split('-')[0].lower()}.{nom.lower()}@enset-douala.cm"
                email = base
                sfx   = 1
                while email in emails_utilises:
                    email = f"{prenom.split('-')[0].lower()}.{nom.lower()}{sfx}@enset-douala.cm"
                    sfx  += 1
                emails_utilises.add(email)

                etu = Etudiant(
                    matricule=matricule, nom=nom, prenom=prenom,
                    date_naissance=_ddn(), lieu_naissance=random.choice(VILLES),
                    filiere=code_fil, niveau=niveau, cycle=cycle,
                    type_etudiant=random.choices(
                        ["REGULIER", "AUDITEUR_LIBRE", "FONCTIONNAIRE"],
                        weights=[72, 14, 14],
                    )[0],
                    statut_fonctionnaire=random.choices([False, True], weights=[80, 20])[0],
                    email=email, telephone=_tel(), sexe=sexe,
                    promotion=ANNEE, annee_academique=ANNEE, actif=True,
                )
                etu.set_password(matricule)
                db.session.add(etu)
                db.session.flush()

                dossier = DossierDiplomation(
                    matricule=matricule, statut='DEPOSE',
                    date_depot=_depot(), annee_academique=ANNEE,
                    nom_sur_diplome=nom, prenom_sur_diplome=prenom,
                    ddn_sur_diplome=etu.date_naissance,
                    lddn_sur_diplome=etu.lieu_naissance,
                    frais_payes=False, montant_frais=75000,
                    id_representant=rep.id_representant,
                    id_communique=communique.id_communique,
                )
                db.session.add(dossier)

        db.session.commit()
        nb_etu = len(FILIERES) * 5
        print(f"  ✓ {nb_etu} étudiants + dossiers insérés ({len(FILIERES)} filières × 5).")

        # ── 10. Récapitulatif ──────────────────────────────────────────────────
        print()
        print("╔══════════════════════════════════════════════════════════╗")
        print("║        SEED DiploPass 2025-2026 — RÉCAPITULATIF          ║")
        print("╠══════════════════════════════════════════════════════════╣")
        print("║  COMPTES STAFF (mdp commun : enset2025)                  ║")
        print("╠══════════════════════════════════════════════════════════╣")
        comptes = [
            ("Admin",          "admin",          "admin1234"),
            ("Directeur",      "jean.fouda",      MDP_STAFF),
            ("Chef Scolarité", "brigitte.ella",   MDP_STAFF),
            ("Chef Bureau",    "samuel.bello",    MDP_STAFF),
        ]
        for role, login, mdp in comptes:
            print(f"║  {role:<18} {login:<22} {mdp:<12} ║")
        print("╠══════════════════════════════════════════════════════════╣")
        print("║  REPRÉSENTANTS DE DÉPARTEMENT                            ║")
        print("╠══════════════════════════════════════════════════════════╣")
        for code_dept, nom, prenom, login in REPS:
            nom_complet = f"{prenom} {nom}"
            dept_nom = next(n for c, n in DEPARTEMENTS if c == code_dept)
            print(f"║  {code_dept:<6} {nom_complet:<22} {login:<22} ║")
        print("╠══════════════════════════════════════════════════════════╣")
        print("║  FILIÈRES (22 au total)                                  ║")
        print("╠══════════════════════════════════════════════════════════╣")
        for code_fil, nom_fil, code_dept in FILIERES:
            print(f"║  {code_dept:<6} › {code_fil:<5} {nom_fil:<35} ║")
        print("╠══════════════════════════════════════════════════════════╣")
        print(f"║  ÉTUDIANTS — {nb_etu} comptes, mdp = matricule              ║")
        print(f"║  Exemples : 25BTP001 / 25ET003 / 25TIC005               ║")
        print("╚══════════════════════════════════════════════════════════╝")


if __name__ == "__main__":
    seed()
