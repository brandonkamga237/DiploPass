#!/usr/bin/env python3
"""
seed.py — Peuplement complet de la base DigiPass
=================================================

Comptes créés (mdp = enset2025 pour tout le monde sauf admin) :

  RÔLE                   NOM COMPLET                  LOGIN              MDP
  ─────────────────────────────────────────────────────────────────────────────
  Admin (existant)       Système Admin                admin              admin1234
  Directeur              FOUDA Jean-Pierre            jean.fouda         enset2025
  Chef Service Scolarité ELLA Brigitte-Marie          brigitte.ella      enset2025
  Chef Bureau Diplom.    BELLO Samuel                 samuel.bello       enset2025

  REPRÉSENTANTS (login = prenom.nom, mdp = enset2025)
  ─────────────────────────────────────────────────────────────────────────────
  GI  Génie Informatique         NKOA Rodrigue          rodrigue.nkoa
  GE  Génie Électrique           FEUSSI Patrick         patrick.feussi
  GC  Génie Civil                ONDOA Guy              guy.ondoa
  GM  Génie Mécanique            TCHAMBA Josué          josue.tchamba
  MAT Mathématiques              FOSSI Armand           armand.fossi
  PHY Physique                   TALLA André            andre.talla
  SI  Sciences Industrielles     WAFFO Lionel           lionel.waffo
  STI Sci. & Tech. Industrielles YOUMBI Franck          franck.youmbi
  SPC Sciences Physiques/Chim.   KENFACK Stève          steve.kenfack
  EEA Électronique/Énergie/Auto  NGUEFACK Ulrich        ulrich.nguefack

  ÉTUDIANTS — 100 au total, 10 par filière
  Login = matricule (ex: 25GI001)   MDP = matricule

Usage :
    python seed.py
"""

import datetime
import random

from app import create_app, db

ANNEE      = "2025-2026"
MDP_STAFF  = "enset2025"

# ─── Pool de noms camerounais pour les étudiants ──────────────────────────────

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

FILIERES = [
    ("GI",  "Génie Informatique"),
    ("GE",  "Génie Électrique"),
    ("GC",  "Génie Civil"),
    ("GM",  "Génie Mécanique"),
    ("MAT", "Mathématiques"),
    ("PHY", "Physique"),
    ("SI",  "Sciences Industrielles"),
    ("STI", "Sciences & Technologies Industrielles"),
    ("SPC", "Sciences Physiques & Chimiques"),
    ("EEA", "Électronique, Énergie & Automatique"),
]

# Tous les étudiants démarrent au statut DEPOSE — aucune pièce téléversée.
# Les vrais documents seront uploadés via l'interface pendant les tests.
STATUTS_PAR_FILIERE = ["DEPOSE"] * 10

#  (code_filiere, nom, prenom, login)  — logins SANS accents pour éviter les pb de saisie
REPS = [
    ("GI",  "NKOA",     "Rodrigue",  "rodrigue.nkoa"),
    ("GE",  "FEUSSI",   "Patrick",   "patrick.feussi"),
    ("GC",  "ONDOA",    "Guy",       "guy.ondoa"),
    ("GM",  "TCHAMBA",  "Josue",     "josue.tchamba"),
    ("MAT", "FOSSI",    "Armand",    "armand.fossi"),
    ("PHY", "TALLA",    "Andre",     "andre.talla"),
    ("SI",  "WAFFO",    "Lionel",    "lionel.waffo"),
    ("STI", "YOUMBI",   "Franck",    "franck.youmbi"),
    ("SPC", "KENFACK",  "Steve",     "steve.kenfack"),
    ("EEA", "NGUEFACK", "Ulrich",    "ulrich.nguefack"),
]

OBSERVATIONS_INCOMPLET = [
    "Acte de naissance manquant.",
    "Photocopie du baccalauréat illisible.",
    "Reçus de frais de scolarité incomplets (année 2023-2024).",
    "Photo d'identité non conforme (fond non blanc).",
    "Fiche d'inscription non signée par le Directeur.",
    "CNI expirée — photocopie non valable.",
]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _ddn():
    return datetime.date(
        random.randint(1998, 2004),
        random.randint(1, 12),
        random.randint(1, 28),
    )

def _tel():
    prefix  = random.choice(["6", "6", "6", "2"])
    digits  = "".join(str(random.randint(0, 9)) for _ in range(7))
    return f"+237 {prefix}{digits[:2]} {digits[2:4]} {digits[4:6]} {digits[6:]}"

def _depot():
    start = datetime.datetime(2025, 9, 15)
    end   = datetime.datetime(2026, 2, 20)
    return start + datetime.timedelta(days=random.randint(0, (end - start).days))


# ─── Seed principal ───────────────────────────────────────────────────────────

def seed():
    app = create_app()
    with app.app_context():

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
        db.session.commit()
        print("  ✓ Tables purgées.")

        # ── 1. Année 2025-2026 ────────────────────────────────────────────────
        annee_obj = AnneeDiplomation.query.filter_by(code=ANNEE).first()
        if not annee_obj:
            annee_obj = AnneeDiplomation(code=ANNEE, actif=True, processus_lance=False)
            db.session.add(annee_obj)
            db.session.flush()
        print(f"  ✓ Année {ANNEE} OK.")

        # ── 2. Directeur : FOUDA Jean-Pierre ─────────────────────────────────
        directeur = Directeur(
            nom="FOUDA",
            prenom="Jean-Pierre",
            grade="Professeur des Universités",
            login="jean.fouda",
            actif=True,
        )
        directeur.set_password(MDP_STAFF)
        db.session.add(directeur)
        db.session.flush()
        print(f"  ✓ Directeur       → jean.fouda        / {MDP_STAFF}")

        # ── 3. Chef Service Scolarité : ELLA Brigitte-Marie ───────────────────
        chef_service = ChefServiceScolarite(
            nom="ELLA",
            prenom="Brigitte-Marie",
            login="brigitte.ella",
            actif=True,
        )
        chef_service.set_password(MDP_STAFF)
        db.session.add(chef_service)
        db.session.flush()
        print(f"  ✓ Chef Service    → brigitte.ella     / {MDP_STAFF}")

        # ── 4. Chef Bureau Diplomation : BELLO Samuel ─────────────────────────
        #   RepresentantFiliere avec est_chef_bureau=True (rôle 'chef_bureau')
        chef_bureau = RepresentantFiliere(
            nom="BELLO",
            prenom="Samuel",
            login="samuel.bello",
            filiere_geree="GI",
            code_filiere="GI",
            bureau="Bureau de la Diplomation",
            est_chef_bureau=True,
            actif=True,
        )
        chef_bureau.set_password(MDP_STAFF)
        db.session.add(chef_bureau)
        db.session.flush()
        print(f"  ✓ Chef Bureau     → samuel.bello      / {MDP_STAFF}")

        # ── 5. Représentants de filière ───────────────────────────────────────
        representants = {}

        # Prénoms affichés avec accents, logins sans accents (définis dans REPS)
        PRENOMS_AFFICHES = {
            "josue.tchamba":    "Josué",
            "andre.talla":      "André",
            "steve.kenfack":    "Stève",
        }

        for code, nom, prenom, login in REPS:
            prenom_affiche = PRENOMS_AFFICHES.get(login, prenom)
            rep = RepresentantFiliere(
                nom=nom,
                prenom=prenom_affiche,
                login=login,
                filiere_geree=code,
                code_filiere=code,
                est_chef_bureau=False,
                actif=True,
            )
            rep.set_password(MDP_STAFF)
            db.session.add(rep)
            db.session.flush()
            representants[code] = rep
            print(f"  ✓ Rep {code:<5}        → {login:<22} / {MDP_STAFF}")

        # ── 6. Lancer le processus + communiqué ──────────────────────────────
        annee_obj.processus_lance = True
        communique = Communique(
            numero_communique="COMM-2025-001",
            titre="Ouverture du processus de diplomation — Promotion 2025-2026",
            contenu=(
                "Les étudiants finissants de la promotion 2025-2026 sont invités à constituer "
                "et déposer leur dossier de diplomation via la plateforme DigiPass avant le "
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
        print(f"  ✓ Communiqué publié → COMM-2025-001 (signé Jean-Pierre FOUDA)")

        # ── 7. 100 étudiants + dossiers ──────────────────────────────────────
        print("→ Génération des étudiants…")

        noms_utilises   = set()
        emails_utilises = set()

        for code, _ in FILIERES:
            # Mélanger les statuts pour que ce ne soit pas dans le même ordre
            statuts = STATUTS_PAR_FILIERE.copy()
            random.shuffle(statuts)

            for i, statut in enumerate(statuts, start=1):
                # ─ Identité ─
                sexe   = random.choices(["M", "F"], weights=[72, 28])[0]
                prenom = random.choice(PRENOMS_M if sexe == "M" else PRENOMS_F)
                for _ in range(30):
                    nom = random.choice(NOMS)
                    if (nom, prenom) not in noms_utilises:
                        break
                noms_utilises.add((nom, prenom))

                # ─ Matricule : 25GI001, 25GI002, … ─
                matricule = f"25{code}{i:03d}"

                # ─ Cycle / Niveau ─
                cycle  = random.choices(["Licence", "Master"], weights=[65, 35])[0]
                niveau = 3 if cycle == "Licence" else 2

                # ─ Email unique ─
                base  = f"{prenom.split('-')[0].lower()}.{nom.lower()}@enset-douala.cm"
                email = base
                sfx   = 1
                while email in emails_utilises:
                    email = f"{prenom.split('-')[0].lower()}.{nom.lower()}{sfx}@enset-douala.cm"
                    sfx  += 1
                emails_utilises.add(email)

                # ─ Étudiant ─
                etu = Etudiant(
                    matricule=matricule,
                    nom=nom,
                    prenom=prenom,
                    date_naissance=_ddn(),
                    lieu_naissance=random.choice(VILLES),
                    filiere=code,
                    niveau=niveau,
                    cycle=cycle,
                    type_etudiant=random.choices(
                        ["REGULIER", "AUDITEUR_LIBRE", "FONCTIONNAIRE"],
                        weights=[72, 14, 14],
                    )[0],
                    statut_fonctionnaire=random.choices([False, True], weights=[80, 20])[0],
                    email=email,
                    telephone=_tel(),
                    sexe=sexe,
                    promotion=ANNEE,
                    annee_academique=ANNEE,
                    actif=True,
                )
                etu.set_password(matricule)  # mdp = matricule
                db.session.add(etu)
                db.session.flush()

                # ─ Dossier ─
                dossier = DossierDiplomation(
                    matricule=matricule,
                    statut='DEPOSE',
                    date_depot=_depot(),
                    annee_academique=ANNEE,
                    nom_sur_diplome=nom,
                    prenom_sur_diplome=prenom,
                    ddn_sur_diplome=etu.date_naissance,
                    lddn_sur_diplome=etu.lieu_naissance,
                    frais_payes=False,
                    montant_frais=75000,
                    id_representant=representants[code].id_representant,
                    id_communique=communique.id_communique,
                )
                db.session.add(dossier)

        db.session.commit()
        print(f"  ✓ 100 étudiants + dossiers insérés.")

        # ── 8. Récapitulatif final ────────────────────────────────────────────
        from collections import Counter
        distrib = Counter(d.statut for d in DossierDiplomation.query.all())

        print()
        print("╔══════════════════════════════════════════════════════════╗")
        print("║         SEED DigiPass 2025-2026 — RÉCAPITULATIF          ║")
        print("╠══════════════════════════════════════════════════════════╣")
        print("║  COMPTES STAFF (mdp commun : enset2025)                  ║")
        print("╠══════════════════════════════════════════════════════════╣")
        comptes = [
            ("Admin",           "admin",            "admin1234"),
            ("Directeur",       "jean.fouda",        MDP_STAFF),
            ("Chef Scolarité",  "brigitte.ella",     MDP_STAFF),
            ("Chef Bureau",     "samuel.bello",      MDP_STAFF),
        ]
        for role, login, mdp in comptes:
            print(f"║  {role:<18} {login:<22} {mdp:<12} ║")
        print("╠══════════════════════════════════════════════════════════╣")
        print("║  REPRÉSENTANTS DE FILIÈRE                                ║")
        print("╠══════════════════════════════════════════════════════════╣")
        for code, nom, prenom, login in REPS:
            nom_complet = f"{prenom} {nom}"
            print(f"║  {code:<5} {nom_complet:<22} {login:<22}  ║")
        print("╠══════════════════════════════════════════════════════════╣")
        print("║  ÉTUDIANTS — 100 comptes, mdp = matricule                ║")
        print("║  Exemples : 25GI001 / 25GE003 / 25MAT007                 ║")
        print("╠══════════════════════════════════════════════════════════╣")
        print("║  RÉPARTITION DES DOSSIERS PAR STATUT                     ║")
        print("╠══════════════════════════════════════════════════════════╣")
        ordre = [
            "DEPOSE", "EN_VERIFICATION", "INCOMPLET", "AUTHENTIFICATION",
            "LISTE_FINISSANTS", "IMPRESSION_PROVISOIRE",
            "PRODUCTION_DEFINITIVE", "SIGNATURE_DIRECTEUR", "CLOTURE",
        ]
        for s in ordre:
            n   = distrib.get(s, 0)
            bar = "█" * n
            print(f"║  {s:<28} {n:3}  {bar:<20} ║")
        print("╚══════════════════════════════════════════════════════════╝")


if __name__ == "__main__":
    seed()
