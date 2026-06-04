from app import create_app, db

app = create_app()

with app.app_context():
    from app.models.admin import Admin
    from app.models.departement import Departement
    from app.models.filiere import Filiere
    from app.models.annee_diplomation import AnneeDiplomation
    from app.models.etudiant import Etudiant
    from app.models.dossier_diplomation import DossierDiplomation

    # ── Admin par défaut ──────────────────────────────────────────────────────
    if not Admin.query.first():
        admin = Admin(nom='Système', prenom='Admin', login='admin', actif=True)
        admin.set_password('admin1234')
        db.session.add(admin)
        db.session.commit()
        print('[DiploPass] Compte admin créé : login=admin / mdp=admin1234')

    # ── Départements et filières réels de l'ENSET ─────────────────────────────
    # Format : (code_dept, nom_dept, [(code_filiere, nom_filiere, cycle), ...])
    STRUCTURE = [
        ('GCI',   'Génie Civil', [
            ('BTP', 'Bâtiment et Travaux Publics',         'Licence/Master'),
            ('GT',  'Géomètre Topographe',                 'Licence/Master'),
            ('ISA', 'Installation Sanitaire et Assainissement', 'Licence/Master'),
        ]),
        ('GEL',   'Génie Électrique', [
            ('EN', 'Électronique',        'Licence/Master'),
            ('ET', 'Électrotechnique',    'Licence/Master'),
            ('FC', 'Froid et Climatisation', 'Licence/Master'),
            ('TE', 'Thermique et Énergie',   'Licence/Master'),
        ]),
        ('GME',   'Génie Mécanique', [
            ('CM', 'Construction Mécanique', 'Licence/Master'),
            ('FM', 'Fabrication Mécanique',  'Licence/Master'),
            ('MA', 'Mécanique Automobile',   'Licence/Master'),
        ]),
        ('STEG',  'Sciences et Techniques Éco. et de Gestion', [
            ('CF',  'Comptabilité et Finance', 'Licence/Master'),
            ('ECO', 'Économie',                'Licence/Master'),
            ('MKG', 'Marketing',               'Licence/Master'),
        ]),
        ('TAD',   'Techniques Administratives', [
            ('CA', 'Communication Administrative', 'Licence/Master'),
        ]),
        ('ESF',   'Économie Sociale et Familiale', [
            ('ESF', 'Économie Sociale et Familiale', 'Licence/Master'),
        ]),
        ('ITH',   'Industrie Textile et de l\'Habillement', [
            ('ITH', 'Industrie Textiles et de l\'Habillement', 'Licence/Master'),
        ]),
        ('GFO',   'Génie Forestier', [
            ('STB', 'Sciences et Technologie du Bois', 'Licence/Master'),
        ]),
        ('GCH',   'Génie Chimique', [
            ('GCH', 'Chimie Industrielle', 'Licence/Master'),
        ]),
        ('GINFO', 'Génie Informatique', [
            ('II',  'Informatique Industriel',                          'Licence/Master'),
            ('TIC', 'Technologie de l\'Information et de la Communication', 'Licence/Master'),
        ]),
        ('SED',   'Sciences de l\'Éducation', [
            ('CO', 'Conseil d\'Orientation', 'Licence/Master'),
        ]),
        ('ESB',   'Enseignement Scientifique de Base', [
            ('IM', 'Ingénierie Mathématique', 'Licence/Master'),
        ]),
    ]

    codes_depts    = {d.code for d in Departement.query.all()}
    codes_filieres = {f.code for f in Filiere.query.all()}

    for code_dept, nom_dept, filieres in STRUCTURE:
        if code_dept not in codes_depts:
            db.session.add(Departement(code=code_dept, nom=nom_dept))
            codes_depts.add(code_dept)

        for code_f, nom_f, cycle_f in filieres:
            if code_f not in codes_filieres:
                db.session.add(Filiere(
                    code=code_f, nom=nom_f, cycle=cycle_f,
                    code_departement=code_dept,
                ))
                codes_filieres.add(code_f)

    db.session.commit()
    print(f'[DiploPass] Structure ENSET : {len(codes_depts)} depts, {len(codes_filieres)} filières.')

    # ── Années académiques ────────────────────────────────────────────────────
    ANNEE_COURANTE = '2025-2026'

    # Années parasites à supprimer (code invalide OU années de test à retirer)
    ANNEES_A_SUPPRIMER = {'2024-2025', '2025-2025'}

    # 1. Supprimer les années indésirables et migrer leurs données
    for annee in AnneeDiplomation.query.all():
        parties = annee.code.split('-')
        code_invalide = len(parties) != 2 or parties[0] == parties[1]
        if (code_invalide or annee.code in ANNEES_A_SUPPRIMER) and annee.code != ANNEE_COURANTE:
            nb_etu = Etudiant.query.filter_by(annee_academique=annee.code).count()
            nb_dos = DossierDiplomation.query.filter_by(annee_academique=annee.code).count()
            if nb_etu or nb_dos:
                Etudiant.query.filter_by(annee_academique=annee.code).update(
                    {'annee_academique': ANNEE_COURANTE}
                )
                DossierDiplomation.query.filter_by(annee_academique=annee.code).update(
                    {'annee_academique': ANNEE_COURANTE}
                )
            db.session.delete(annee)
            print(
                f'[DiploPass] Année invalide « {annee.code} » supprimée'
                + (f', {nb_etu} étudiant(s) et {nb_dos} dossier(s) migrés vers {ANNEE_COURANTE}.'
                   if nb_etu or nb_dos else '.')
            )
    db.session.commit()

    # 2. S'assurer que l'année courante existe
    if not AnneeDiplomation.query.filter_by(code=ANNEE_COURANTE).first():
        db.session.add(AnneeDiplomation(code=ANNEE_COURANTE))
        db.session.commit()
        print(f'[DiploPass] Année {ANNEE_COURANTE} créée.')

    # 3. Rattacher les étudiants/dossiers sans année à l'année courante
    orphelins_etu = Etudiant.query.filter(
        (Etudiant.annee_academique == None) |  # noqa: E711
        (Etudiant.annee_academique == '')
    ).all()
    if orphelins_etu:
        for e in orphelins_etu:
            e.annee_academique = ANNEE_COURANTE
        db.session.commit()
        print(f'[DiploPass] {len(orphelins_etu)} étudiant(s) rattaché(s) à {ANNEE_COURANTE}.')

    orphelins_dos = DossierDiplomation.query.filter(
        (DossierDiplomation.annee_academique == None) |  # noqa: E711
        (DossierDiplomation.annee_academique == '')
    ).all()
    if orphelins_dos:
        for d in orphelins_dos:
            d.annee_academique = ANNEE_COURANTE
        db.session.commit()
        print(f'[DiploPass] {len(orphelins_dos)} dossier(s) rattaché(s) à {ANNEE_COURANTE}.')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
