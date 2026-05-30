from app import create_app, db

app = create_app()

with app.app_context():
    from app.models.admin import Admin
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
        print('[DigiPass] Compte admin créé : login=admin / mdp=admin1234')

    # ── Filières ENSET de base ────────────────────────────────────────────────
    FILIERES_BASE = [
        ('GI',   'Génie Informatique',                    'Licence/Master'),
        ('GE',   'Génie Électrique',                      'Licence/Master'),
        ('GC',   'Génie Civil',                           'Licence/Master'),
        ('GM',   'Génie Mécanique',                       'Licence/Master'),
        ('MAT',  'Mathématiques',                         'Licence/Master'),
        ('PHY',  'Physique',                              'Licence/Master'),
        ('SI',   'Sciences Industrielles',                'Licence/Master'),
        ('STI',  'Sciences & Technologies Industrielles', 'Licence'),
        ('SPC',  'Sciences Physiques & Chimiques',        'Licence/Master'),
        ('EEA',  'Électronique, Énergie & Automatique',  'Licence/Master'),
    ]
    codes_existants = {f.code for f in Filiere.query.all()}
    nouvelles = [
        Filiere(code=c, nom=n, cycle=cy)
        for c, n, cy in FILIERES_BASE if c not in codes_existants
    ]
    if nouvelles:
        db.session.add_all(nouvelles)
        db.session.commit()
        print(f'[DigiPass] {len(nouvelles)} filière(s) de base créée(s).')

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
                f'[DigiPass] Année invalide « {annee.code} » supprimée'
                + (f', {nb_etu} étudiant(s) et {nb_dos} dossier(s) migrés vers {ANNEE_COURANTE}.'
                   if nb_etu or nb_dos else '.')
            )
    db.session.commit()

    # 2. S'assurer que l'année courante existe
    if not AnneeDiplomation.query.filter_by(code=ANNEE_COURANTE).first():
        db.session.add(AnneeDiplomation(code=ANNEE_COURANTE))
        db.session.commit()
        print(f'[DigiPass] Année {ANNEE_COURANTE} créée.')

    # 3. Rattacher les étudiants/dossiers sans année à l'année courante
    orphelins_etu = Etudiant.query.filter(
        (Etudiant.annee_academique == None) |  # noqa: E711
        (Etudiant.annee_academique == '')
    ).all()
    if orphelins_etu:
        for e in orphelins_etu:
            e.annee_academique = ANNEE_COURANTE
        db.session.commit()
        print(f'[DigiPass] {len(orphelins_etu)} étudiant(s) rattaché(s) à {ANNEE_COURANTE}.')

    orphelins_dos = DossierDiplomation.query.filter(
        (DossierDiplomation.annee_academique == None) |  # noqa: E711
        (DossierDiplomation.annee_academique == '')
    ).all()
    if orphelins_dos:
        for d in orphelins_dos:
            d.annee_academique = ANNEE_COURANTE
        db.session.commit()
        print(f'[DigiPass] {len(orphelins_dos)} dossier(s) rattaché(s) à {ANNEE_COURANTE}.')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
