from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_required
from app.utils.decorators import role_required
from app.models.directeur import Directeur
from app.models.chef_service import ChefServiceScolarite
from app.models.representant import RepresentantFiliere
from app.models.departement import Departement
from app.models.filiere import Filiere
from app.models.annee_diplomation import AnneeDiplomation
from app.models.etudiant import Etudiant
from app.models.liste_finissants import ListeFinissants
from app.services.import_service import importer_etudiants_json
from app import db
import json

_ROLES_MODELES = {
    'directeur':    Directeur,
    'chef_service': ChefServiceScolarite,
    'representant': RepresentantFiliere,
}

admin_bp = Blueprint('admin', __name__)


# ── Dashboard ────────────────────────────────────────────────────────────────

@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    from app.models.dossier_diplomation import DossierDiplomation
    annee = session.get('annee_active_code')
    nb_etudiants_annee = (
        Etudiant.query.filter_by(annee_academique=annee).count() if annee
        else Etudiant.query.count()
    )
    nb_dossiers_annee = (
        DossierDiplomation.query.filter_by(annee_academique=annee).count() if annee
        else DossierDiplomation.query.count()
    )
    return render_template(
        'admin/dashboard.html',
        nb_etudiants=nb_etudiants_annee,
        nb_dossiers=nb_dossiers_annee,
        nb_directeurs=Directeur.query.count(),
        nb_representants=RepresentantFiliere.query.count(),
        nb_chefs_bureau=RepresentantFiliere.query.filter_by(est_chef_bureau=True).count(),
        nb_chefs_service=ChefServiceScolarite.query.count(),
        nb_filieres=Filiere.query.count(),
        nb_departements=Departement.query.count(),
        nb_annees=AnneeDiplomation.query.count(),
    )


# ── Gestion des années de diplomation ────────────────────────────────────────

@admin_bp.route('/annees')
@login_required
@role_required('admin')
def liste_annees():
    from app.models.dossier_diplomation import DossierDiplomation
    STATUTS_FINAUX = ['CLOTURE', 'REJETE']
    annees = AnneeDiplomation.query.order_by(AnneeDiplomation.code.desc()).all()
    for a in annees:
        a._nb_etudiants = Etudiant.query.filter_by(annee_academique=a.code).count()
        a._nb_dossiers = DossierDiplomation.query.filter_by(annee_academique=a.code).count()
        a._nb_en_cours = (
            DossierDiplomation.query
            .filter_by(annee_academique=a.code)
            .filter(DossierDiplomation.statut.notin_(STATUTS_FINAUX))
            .count()
        )
    return render_template('admin/annees.html', annees=annees)


@admin_bp.route('/annees/nouvelle', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def nouvelle_annee():
    if request.method == 'POST':
        from app.models.dossier_diplomation import DossierDiplomation
        code = request.form.get('code', '').strip()
        if not code:
            flash('Le code est obligatoire.', 'danger')
            return redirect(url_for('admin.liste_annees'))
        if AnneeDiplomation.query.filter_by(code=code).first():
            flash(f'L\'année « {code} » existe déjà.', 'warning')
            return redirect(url_for('admin.liste_annees'))
        # Bloquer si un processus est encore en cours (dossiers non clôturés)
        STATUTS_FINAUX = ['CLOTURE', 'REJETE']
        for a in AnneeDiplomation.query.filter_by(processus_lance=True).all():
            nb_en_cours = (
                DossierDiplomation.query
                .filter_by(annee_academique=a.code)
                .filter(DossierDiplomation.statut.notin_(STATUTS_FINAUX))
                .count()
            )
            if nb_en_cours > 0:
                flash(
                    f'Impossible de créer une nouvelle année : le processus '
                    f'« {a.code} » est encore en cours '
                    f'({nb_en_cours} dossier(s) non clôturé(s)).',
                    'danger',
                )
                return redirect(url_for('admin.liste_annees'))
        db.session.add(AnneeDiplomation(code=code))
        db.session.commit()
        session['annee_active_code'] = code
        flash(f'Année {code} créée.', 'success')
        return redirect(url_for('admin.liste_annees'))
    return redirect(url_for('admin.liste_annees'))


@admin_bp.route('/annees/<int:id>/supprimer', methods=['POST'])
@login_required
@role_required('admin')
def supprimer_annee(id):
    from app.models.dossier_diplomation import DossierDiplomation
    annee = AnneeDiplomation.query.get_or_404(id)
    nb_etu = Etudiant.query.filter_by(annee_academique=annee.code).count()
    nb_dos = DossierDiplomation.query.filter_by(annee_academique=annee.code).count()
    if nb_etu > 0 or nb_dos > 0:
        flash(
            f'Impossible de supprimer {annee.code} : '
            f'{nb_etu} étudiant(s) et {nb_dos} dossier(s) y sont rattachés.',
            'danger',
        )
        return redirect(url_for('admin.liste_annees'))
    db.session.delete(annee)
    db.session.commit()
    flash(f'Année {annee.code} supprimée.', 'success')
    return redirect(url_for('admin.liste_annees'))


# ── Gestion des départements ──────────────────────────────────────────────────

@admin_bp.route('/departements')
@login_required
@role_required('admin')
def liste_departements():
    departements = Departement.query.order_by(Departement.nom).all()
    return render_template('admin/departements.html', departements=departements)


@admin_bp.route('/departements/nouveau', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def nouveau_departement():
    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        nom  = request.form.get('nom', '').strip()
        if not code or not nom:
            flash('Le code et le nom sont obligatoires.', 'danger')
            return redirect(request.url)
        if Departement.query.get(code):
            flash(f'Un département avec le code « {code} » existe déjà.', 'warning')
            return redirect(request.url)
        db.session.add(Departement(code=code, nom=nom, actif=True))
        db.session.commit()
        flash(f'Département {nom} créé.', 'success')
        return redirect(url_for('admin.liste_departements'))
    return render_template('admin/nouveau_departement.html')


@admin_bp.route('/departements/<code>/toggle', methods=['POST'])
@login_required
@role_required('admin')
def toggle_departement(code):
    d = Departement.query.get_or_404(code)
    d.actif = not d.actif
    db.session.commit()
    flash(f'Département {d.nom} {"activé" if d.actif else "désactivé"}.', 'info')
    return redirect(url_for('admin.liste_departements'))


# ── Gestion des filières ──────────────────────────────────────────────────────

@admin_bp.route('/filieres')
@login_required
@role_required('admin')
def liste_filieres():
    departements = Departement.query.order_by(Departement.nom).all()
    filieres = Filiere.query.order_by(Filiere.code_departement, Filiere.nom).all()
    return render_template('admin/filieres.html', filieres=filieres, departements=departements)


@admin_bp.route('/filieres/nouvelle', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def nouvelle_filiere():
    departements = Departement.query.order_by(Departement.nom).all()
    if request.method == 'POST':
        code         = request.form.get('code', '').strip().upper()
        nom          = request.form.get('nom', '').strip()
        cycle        = request.form.get('cycle', '').strip()
        code_dept    = request.form.get('code_departement', '').strip() or None
        if not code or not nom:
            flash('Le code et le nom sont obligatoires.', 'danger')
            return redirect(request.url)
        if Filiere.query.get(code):
            flash(f'Une filière avec le code « {code} » existe déjà.', 'warning')
            return redirect(request.url)
        db.session.add(Filiere(code=code, nom=nom, cycle=cycle or None,
                               code_departement=code_dept))
        db.session.commit()
        flash(f'Filière {nom} créée.', 'success')
        return redirect(url_for('admin.liste_filieres'))
    return render_template('admin/nouvelle_filiere.html', departements=departements)


@admin_bp.route('/filieres/<code>/toggle', methods=['POST'])
@login_required
@role_required('admin')
def toggle_filiere(code):
    f = Filiere.query.get_or_404(code)
    f.actif = not f.actif
    db.session.commit()
    flash(f'Filière {f.nom} {"activée" if f.actif else "désactivée"}.', 'info')
    return redirect(url_for('admin.liste_filieres'))


# ── Gestion des comptes ───────────────────────────────────────────────────────

@admin_bp.route('/creer-compte', methods=['POST'])
@login_required
@role_required('admin')
def creer_compte():
    role = request.form.get('role', '').strip()
    nom = request.form.get('nom', '').strip().upper()
    prenom = request.form.get('prenom', '').strip()
    login_val = request.form.get('login', '').strip()
    mdp = request.form.get('mot_de_passe', '')

    if not all([role, nom, prenom, login_val, mdp]):
        flash('Tous les champs sont obligatoires.', 'danger')
        return redirect(url_for('admin.liste_comptes'))

    if role in ('representant', 'chef_bureau'):
        filiere_geree = request.form.get('filiere_geree', '').strip()
        if not filiere_geree:
            flash('La filière représentée est obligatoire.', 'danger')
            return redirect(url_for('admin.liste_comptes'))
        is_chef = (role == 'chef_bureau')
        existing = RepresentantFiliere.query.filter_by(
            filiere_geree=filiere_geree, est_chef_bureau=is_chef
        ).first()
        if existing:
            type_label = 'Chef de Bureau de la Diplomation' if is_chef else 'Représentant de filière'
            flash(
                f'Un {type_label} existe déjà pour la filière {filiere_geree} '
                f'({existing.prenom} {existing.nom}). '
                f'Désactivez ce compte avant d\'en créer un nouveau.',
                'danger',
            )
            return redirect(url_for('admin.liste_comptes'))
        compte = RepresentantFiliere(
            nom=nom, prenom=prenom, login=login_val,
            filiere_geree=filiere_geree,
            est_chef_bureau=is_chef,
        )
        compte.set_password(mdp)

    elif role == 'directeur':
        existing = Directeur.query.first()
        if existing:
            flash(
                f'Un directeur existe déjà ({existing.prenom} {existing.nom}). '
                f'Désactivez ce compte avant d\'en créer un nouveau.',
                'danger',
            )
            return redirect(url_for('admin.liste_comptes'))
        compte = Directeur(
            nom=nom, prenom=prenom, login=login_val,
            grade=request.form.get('grade', '').strip(),
        )
        compte.set_password(mdp)

    elif role == 'chef_service':
        existing = ChefServiceScolarite.query.first()
        if existing:
            flash(
                f'Un Chef de Scolarité existe déjà ({existing.prenom} {existing.nom}). '
                f'Désactivez ce compte avant d\'en créer un nouveau.',
                'danger',
            )
            return redirect(url_for('admin.liste_comptes'))
        compte = ChefServiceScolarite(nom=nom, prenom=prenom, login=login_val)
        compte.set_password(mdp)

    else:
        flash('Rôle invalide.', 'danger')
        return redirect(url_for('admin.liste_comptes'))

    db.session.add(compte)
    db.session.commit()
    flash(f'Compte créé : {prenom} {nom} ({role.replace("_", " ").title()}).', 'success')
    return redirect(url_for('admin.liste_comptes'))


@admin_bp.route('/comptes')
@login_required
@role_required('admin')
def liste_comptes():
    filieres = Filiere.query.filter_by(actif=True).order_by(Filiere.nom).all()
    return render_template(
        'admin/liste_comptes.html',
        directeurs=Directeur.query.order_by(Directeur.nom).all(),
        chefs_service=ChefServiceScolarite.query.order_by(ChefServiceScolarite.nom).all(),
        representants=RepresentantFiliere.query.order_by(
            RepresentantFiliere.est_chef_bureau.desc(),
            RepresentantFiliere.nom,
        ).all(),
        filieres=filieres,
    )


@admin_bp.route('/comptes/directeur/<int:id>/modifier', methods=['POST'])
@login_required
@role_required('admin')
def modifier_directeur(id):
    d = Directeur.query.get_or_404(id)
    d.nom    = request.form.get('nom', d.nom).strip().upper()
    d.prenom = request.form.get('prenom', d.prenom).strip()
    d.login  = request.form.get('login', d.login).strip()
    d.grade  = request.form.get('grade', '').strip()
    mdp = request.form.get('nouveau_mdp', '').strip()
    if mdp:
        if len(mdp) < 6:
            flash('Mot de passe trop court — autres modifications enregistrées.', 'warning')
        else:
            d.set_password(mdp)
    db.session.commit()
    flash(f'{d.prenom} {d.nom} mis à jour.', 'success')
    return redirect(url_for('admin.liste_comptes'))


@admin_bp.route('/comptes/chef-service/<int:id>/modifier', methods=['POST'])
@login_required
@role_required('admin')
def modifier_chef_service(id):
    cs = ChefServiceScolarite.query.get_or_404(id)
    cs.nom    = request.form.get('nom', cs.nom).strip().upper()
    cs.prenom = request.form.get('prenom', cs.prenom).strip()
    cs.login  = request.form.get('login', cs.login).strip()
    mdp = request.form.get('nouveau_mdp', '').strip()
    if mdp:
        if len(mdp) < 6:
            flash('Mot de passe trop court — autres modifications enregistrées.', 'warning')
        else:
            cs.set_password(mdp)
    db.session.commit()
    flash(f'{cs.prenom} {cs.nom} mis à jour.', 'success')
    return redirect(url_for('admin.liste_comptes'))


@admin_bp.route('/comptes/representant/<int:id>/modifier', methods=['POST'])
@login_required
@role_required('admin')
def modifier_representant(id):
    r = RepresentantFiliere.query.get_or_404(id)
    r.nom          = request.form.get('nom', r.nom).strip().upper()
    r.prenom       = request.form.get('prenom', r.prenom).strip()
    r.login        = request.form.get('login', r.login).strip()
    r.filiere_geree = request.form.get('filiere_geree', r.filiere_geree).strip()
    mdp = request.form.get('nouveau_mdp', '').strip()
    if mdp:
        if len(mdp) < 6:
            flash('Mot de passe trop court — autres modifications enregistrées.', 'warning')
        else:
            r.set_password(mdp)
    db.session.commit()
    flash(f'{r.prenom} {r.nom} mis à jour.', 'success')
    return redirect(url_for('admin.liste_comptes'))


@admin_bp.route('/comptes/directeur/<int:id>/toggle-actif', methods=['POST'])
@login_required
@role_required('admin')
def toggle_directeur(id):
    d = Directeur.query.get_or_404(id)
    d.actif = not d.actif
    db.session.commit()
    flash(f'Compte de {d.prenom} {d.nom} {"activé" if d.actif else "désactivé"}.', 'info')
    return redirect(url_for('admin.liste_comptes'))


@admin_bp.route('/comptes/chef-service/<int:id>/toggle-actif', methods=['POST'])
@login_required
@role_required('admin')
def toggle_chef_service(id):
    cs = ChefServiceScolarite.query.get_or_404(id)
    cs.actif = not cs.actif
    db.session.commit()
    flash(f'Compte de {cs.prenom} {cs.nom} {"activé" if cs.actif else "désactivé"}.', 'info')
    return redirect(url_for('admin.liste_comptes'))


@admin_bp.route('/comptes/<string:type_compte>/<int:id>/reset-mdp', methods=['POST'])
@login_required
@role_required('admin')
def reset_mdp(type_compte, id):
    nouveau_mdp = request.form.get('nouveau_mdp', '').strip()
    if len(nouveau_mdp) < 6:
        flash('Le mot de passe doit faire au moins 6 caractères.', 'danger')
        return redirect(url_for('admin.liste_comptes'))
    modele = _ROLES_MODELES.get(type_compte)
    if not modele:
        flash('Type de compte inconnu.', 'danger')
        return redirect(url_for('admin.liste_comptes'))
    compte = modele.query.get_or_404(id)
    compte.set_password(nouveau_mdp)
    db.session.commit()
    flash(f'Mot de passe réinitialisé pour {compte.prenom} {compte.nom}.', 'success')
    return redirect(url_for('admin.liste_comptes'))


@admin_bp.route('/comptes/representant/<int:id>/nommer-chef-bureau', methods=['POST'])
@login_required
@role_required('admin')
def nommer_chef_bureau(id):
    rep = RepresentantFiliere.query.get_or_404(id)
    rep.est_chef_bureau = True
    db.session.commit()
    flash(f'{rep.nom_complet} est maintenant Chef de Bureau de la Diplomation.', 'success')
    return redirect(url_for('admin.liste_comptes'))


@admin_bp.route('/comptes/representant/<int:id>/retirer-chef-bureau', methods=['POST'])
@login_required
@role_required('admin')
def retirer_chef_bureau(id):
    rep = RepresentantFiliere.query.get_or_404(id)
    rep.est_chef_bureau = False
    db.session.commit()
    flash(f'{rep.nom_complet} est à nouveau Représentant de filière uniquement.', 'info')
    return redirect(url_for('admin.liste_comptes'))


@admin_bp.route('/comptes/representant/<int:id>/toggle-actif', methods=['POST'])
@login_required
@role_required('admin')
def toggle_representant(id):
    rep = RepresentantFiliere.query.get_or_404(id)
    rep.actif = not rep.actif
    db.session.commit()
    flash(f'Compte de {rep.nom_complet} {"activé" if rep.actif else "désactivé"}.', 'info')
    return redirect(url_for('admin.liste_comptes'))


# ── Étudiants ─────────────────────────────────────────────────────────────────

@admin_bp.route('/importer-etudiants', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def importer_etudiants():
    annee_active = session.get('annee_active_code')
    if not annee_active:
        flash('Aucune année académique sélectionnée. Créez et sélectionnez une année d\'abord.', 'danger')
        return redirect(url_for('admin.liste_annees'))

    if request.method == 'POST':
        fichier = request.files.get('fichier_json')
        if not fichier or fichier.filename == '':
            flash('Aucun fichier sélectionné.', 'warning')
            return redirect(request.url)
        importes, erreurs, details = importer_etudiants_json(
            fichier, annee_academique=annee_active
        )
        flash(f'{importes} étudiant(s) importé(s) pour {annee_active}, {erreurs} erreur(s).', 'info')
        for d in details:
            flash(d, 'warning')
        if importes > 0:
            from app.models.notification import notifier_tous
            notifier_tous(
                f'Liste des étudiants importée pour {annee_active} — {importes} étudiant(s).',
                type_notif='info',
                lien=None,
            )
            db.session.commit()

    return render_template('admin/importer_etudiants.html', annee_active=annee_active)


@admin_bp.route('/etudiants/creer', methods=['POST'])
@login_required
@role_required('admin')
def creer_etudiant():
    from werkzeug.security import generate_password_hash
    annee = session.get('annee_active_code', '')
    matricule = request.form.get('matricule', '').strip()
    nom = request.form.get('nom', '').strip().upper()
    prenom = request.form.get('prenom', '').strip()
    filiere = request.form.get('filiere', '').strip()
    date_naissance = request.form.get('date_naissance', '').strip()
    lieu_naissance = request.form.get('lieu_naissance', '').strip()
    sexe = request.form.get('sexe', '').strip()
    niveau = request.form.get('niveau', '').strip()
    cycle = request.form.get('cycle', 'LICENCE').strip()
    type_etudiant = request.form.get('type_etudiant', 'REGULIER').strip()
    email = request.form.get('email', '').strip() or None
    telephone = request.form.get('telephone', '').strip()

    if not all([matricule, nom, prenom, filiere, date_naissance]):
        flash('Matricule, nom, prénom, filière et date de naissance sont obligatoires.', 'danger')
        return redirect(url_for('admin.liste_etudiants'))
    if Etudiant.query.get(matricule):
        flash(f'Le matricule {matricule} existe déjà.', 'warning')
        return redirect(url_for('admin.liste_etudiants'))

    import datetime as dt
    try:
        ddn = dt.date.fromisoformat(date_naissance)
    except ValueError:
        flash('Date de naissance invalide.', 'danger')
        return redirect(url_for('admin.liste_etudiants'))

    etu = Etudiant(
        matricule=matricule,
        nom=nom,
        prenom=prenom,
        date_naissance=ddn,
        lieu_naissance=lieu_naissance,
        filiere=filiere,
        niveau=int(niveau) if niveau else None,
        cycle=cycle,
        type_etudiant=type_etudiant,
        sexe=sexe,
        email=email,
        telephone=telephone,
        annee_academique=annee,
        mot_de_passe=generate_password_hash(matricule),
    )
    db.session.add(etu)
    db.session.commit()
    flash(f'Étudiant {prenom} {nom} ({matricule}) créé. Mot de passe initial : {matricule}.', 'success')
    return redirect(url_for('admin.liste_etudiants'))


@admin_bp.route('/etudiants')
@login_required
@role_required('admin')
def liste_etudiants():
    annee_active = session.get('annee_active_code')
    annees = AnneeDiplomation.query.order_by(AnneeDiplomation.code.desc()).all()
    filieres = Filiere.query.filter_by(actif=True).order_by(Filiere.nom).all()
    q = Etudiant.query
    if annee_active:
        q = q.filter_by(annee_academique=annee_active)
    etudiants = q.order_by(Etudiant.nom, Etudiant.prenom).all()
    return render_template('admin/liste_etudiants.html',
                           etudiants=etudiants, annees=annees, filieres=filieres,
                           annee_active=annee_active)


@admin_bp.route('/etudiants/<matricule>/modifier', methods=['POST'])
@login_required
@role_required('admin')
def modifier_etudiant(matricule):
    etu = Etudiant.query.get_or_404(matricule)

    etu.nom            = request.form.get('nom', etu.nom).strip().upper()
    etu.prenom         = request.form.get('prenom', etu.prenom).strip()
    etu.filiere        = request.form.get('filiere', etu.filiere).strip()
    etu.niveau         = request.form.get('niveau', etu.niveau) or etu.niveau
    etu.cycle          = request.form.get('cycle', etu.cycle)
    etu.type_etudiant  = request.form.get('type_etudiant', etu.type_etudiant)
    etu.statut_fonctionnaire = request.form.get('statut_fonctionnaire') == '1'
    etu.sexe           = request.form.get('sexe', etu.sexe)
    etu.email          = request.form.get('email', '').strip() or etu.email
    etu.telephone      = request.form.get('telephone', '').strip()
    etu.annee_academique = request.form.get('annee_academique', etu.annee_academique)
    etu.actif          = request.form.get('actif') == '1'

    nouveau_mdp = request.form.get('nouveau_mdp', '').strip()
    if nouveau_mdp:
        if len(nouveau_mdp) < 6:
            flash('Mot de passe trop court (min. 6 caractères) — autres modifications enregistrées.', 'warning')
        else:
            etu.set_password(nouveau_mdp)

    db.session.commit()
    flash(f'{etu.prenom} {etu.nom} mis à jour.', 'success')
    return redirect(url_for('admin.liste_etudiants'))


# ══════════════════════════════════════════════════════════════════
# LISTE DES FINISSANTS
# ══════════════════════════════════════════════════════════════════

@admin_bp.route('/finissants')
@login_required
@role_required('admin')
def liste_finissants():
    annee = session.get('annee_active_code', '')
    finissants = ListeFinissants.query.filter_by(
        annee_academique=annee
    ).order_by(ListeFinissants.nom).all() if annee else []
    annees = AnneeDiplomation.query.order_by(AnneeDiplomation.code.desc()).all()
    annee_obj = AnneeDiplomation.query.filter_by(code=annee).first() if annee else None
    annee_finalisee = annee_obj.liste_finalisee if annee_obj else False
    return render_template('admin/liste_finissants.html',
                           finissants=finissants, annee=annee, annees=annees,
                           annee_finalisee=annee_finalisee)


@admin_bp.route('/finissants/ajouter', methods=['POST'])
@login_required
@role_required('admin')
def ajouter_finissant():
    annee = session.get('annee_active_code', '')
    matricule = request.form.get('matricule', '').strip().upper()
    nom = request.form.get('nom', '').strip().upper()
    prenom = request.form.get('prenom', '').strip()
    filiere = request.form.get('filiere', '').strip().upper()

    if not matricule or not nom or not annee:
        flash('Matricule et nom sont obligatoires.', 'danger')
        return redirect(url_for('admin.liste_finissants'))

    # Pré-remplir depuis la table etudiant si le matricule existe
    etu = Etudiant.query.get(matricule)
    if etu:
        nom = nom or etu.nom
        prenom = prenom or etu.prenom
        filiere = filiere or etu.filiere

    existant = ListeFinissants.query.filter_by(
        matricule=matricule, annee_academique=annee
    ).first()
    if existant:
        flash(f'{matricule} est déjà dans la liste.', 'warning')
        return redirect(url_for('admin.liste_finissants'))

    f = ListeFinissants(matricule=matricule, nom=nom, prenom=prenom,
                        filiere=filiere, annee_academique=annee, valide=True)
    db.session.add(f)
    db.session.commit()
    flash(f'{prenom} {nom} ({matricule}) ajouté à la liste des finissants.', 'success')
    return redirect(url_for('admin.liste_finissants'))


@admin_bp.route('/finissants/importer', methods=['POST'])
@login_required
@role_required('admin')
def importer_finissants():
    annee = session.get('annee_active_code', '')
    if not annee:
        flash("Aucune année académique active.", 'danger')
        return redirect(url_for('admin.liste_finissants'))

    annee_obj = AnneeDiplomation.query.filter_by(code=annee).first()
    if annee_obj and annee_obj.liste_finalisee:
        flash('La liste est déjà finalisée — aucune modification possible.', 'danger')
        return redirect(url_for('admin.liste_finissants'))

    fichier = request.files.get('fichier')
    if not fichier or not fichier.filename.endswith('.json'):
        flash('Fichier JSON requis.', 'danger')
        return redirect(url_for('admin.liste_finissants'))

    try:
        data = json.loads(fichier.read().decode('utf-8'))
        if not isinstance(data, list):
            raise ValueError("Le fichier doit contenir une liste JSON.")

        nb_ajoutes = nb_maj = nb_ignores = 0
        for item in data:
            matricule = str(item.get('matricule', '')).strip().upper()
            nom       = str(item.get('nom', '')).strip().upper()
            prenom    = str(item.get('prenom', '')).strip()
            filiere   = str(item.get('filiere', '')).strip().upper()
            cycle     = str(item.get('cycle', '')).strip()
            niveau    = item.get('niveau')

            if not matricule or not nom:
                nb_ignores += 1
                continue

            # Enrichir depuis la table etudiant si disponible
            etu = Etudiant.query.get(matricule)
            if etu:
                nom    = nom    or etu.nom
                prenom = prenom or etu.prenom
                filiere = filiere or etu.filiere

            existant = ListeFinissants.query.filter_by(
                matricule=matricule, annee_academique=annee
            ).first()
            if existant:
                # Mise à jour si déjà présent
                existant.nom    = nom
                existant.prenom = prenom
                existant.filiere = filiere
                nb_maj += 1
            else:
                db.session.add(ListeFinissants(
                    matricule=matricule, nom=nom, prenom=prenom,
                    filiere=filiere, annee_academique=annee, valide=True
                ))
                nb_ajoutes += 1

        db.session.commit()
        flash(
            f'{nb_ajoutes} ajouté(s), {nb_maj} mis à jour, {nb_ignores} ignoré(s).',
            'success'
        )
        if nb_ajoutes + nb_maj > 0:
            from app.models.notification import notifier_tous
            notifier_tous(
                f'Liste des finissants importée pour {annee} — '
                f'{nb_ajoutes} ajouté(s), {nb_maj} mis à jour.',
                type_notif='success',
            )
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de l\'import : {e}', 'danger')

    return redirect(url_for('admin.liste_finissants'))


@admin_bp.route('/finissants/finaliser', methods=['POST'])
@login_required
@role_required('admin')
def finaliser_liste():
    """
    Finalise la liste des finissants pour l'année active.
    Déclenche automatiquement le cross-référencement :
    - Dossiers AUTHENTIFICATION dont le matricule est dans la liste → LISTE_FINISSANTS
    - Dossiers AUTHENTIFICATION dont le matricule est ABSENT de la liste → NON_ELIGIBLE
    """
    from app.models.dossier_diplomation import DossierDiplomation
    from app.models.historique_phases import HistoriquePhases
    import datetime

    annee = session.get('annee_active_code', '')
    if not annee:
        flash("Aucune année académique active.", 'danger')
        return redirect(url_for('admin.liste_finissants'))

    annee_obj = AnneeDiplomation.query.filter_by(code=annee).first()
    if not annee_obj:
        flash("Année introuvable.", 'danger')
        return redirect(url_for('admin.liste_finissants'))

    if annee_obj.liste_finalisee:
        flash('La liste est déjà finalisée.', 'warning')
        return redirect(url_for('admin.liste_finissants'))

    # Matricules validés sur la liste
    matricules_valides = {
        f.matricule for f in
        ListeFinissants.query.filter_by(annee_academique=annee, valide=True).all()
    }

    if not matricules_valides:
        flash('Impossible de finaliser : la liste est vide.', 'danger')
        return redirect(url_for('admin.liste_finissants'))

    # Dossiers éligibles au cross-référencement (SOUMISSION_PHYSIQUE ou AUTHENTIFICATION)
    from sqlalchemy import or_
    dossiers = DossierDiplomation.query.filter(
        DossierDiplomation.annee_academique == annee,
        or_(
            DossierDiplomation.statut == 'SOUMISSION_PHYSIQUE',
            DossierDiplomation.statut == 'AUTHENTIFICATION',
        )
    ).all()

    nb_eligibles = nb_non_eligibles = 0

    for dossier in dossiers:
        ancien = dossier.statut
        if dossier.matricule in matricules_valides:
            dossier.statut = 'LISTE_FINISSANTS'
            nb_eligibles += 1
            nouveau = 'LISTE_FINISSANTS'
        else:
            dossier.statut = 'NON_ELIGIBLE'
            dossier.observations = (
                "Votre matricule ne figure pas dans la liste officielle "
                "des finissants ayant validé leur année académique. "
                "La diplomation ne peut pas continuer."
            )
            nb_non_eligibles += 1
            nouveau = 'NON_ELIGIBLE'

        db.session.add(HistoriquePhases(
            id_dossier=dossier.id_dossier,
            phase='LISTE_FINISSANTS',
            ancien_statut=ancien,
            nouveau_statut=nouveau,
            commentaire='Finalisation automatique de la liste des finissants',
            id_acteur='admin',
            role_acteur='admin',
            date_action=datetime.datetime.now(),
        ))

    annee_obj.liste_finalisee = True
    db.session.commit()

    flash(
        f'Liste finalisée ✓ — {nb_eligibles} dossier(s) passé(s) en LISTE_FINISSANTS, '
        f'{nb_non_eligibles} marqué(s) NON_ELIGIBLE.',
        'success'
    )
    return redirect(url_for('admin.liste_finissants'))


@admin_bp.route('/finissants/<int:id>/toggle', methods=['POST'])
@login_required
@role_required('admin')
def toggle_finissant(id):
    f = ListeFinissants.query.get_or_404(id)
    f.valide = not f.valide
    if not f.valide:
        f.motif_invalidation = request.form.get('motif', 'Invalidé par l\'admin')
    else:
        f.motif_invalidation = None
    db.session.commit()
    etat = 'validé' if f.valide else 'invalidé'
    flash(f'{f.prenom} {f.nom} ({f.matricule}) — {etat}.', 'success')
    return redirect(url_for('admin.liste_finissants'))


@admin_bp.route('/finissants/<int:id>/supprimer', methods=['POST'])
@login_required
@role_required('admin')
def supprimer_finissant(id):
    f = ListeFinissants.query.get_or_404(id)
    nom = f'{f.prenom} {f.nom}'
    db.session.delete(f)
    db.session.commit()
    flash(f'{nom} supprimé de la liste.', 'success')
    return redirect(url_for('admin.liste_finissants'))
