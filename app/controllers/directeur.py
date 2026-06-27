from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_required, current_user
from app.utils.decorators import role_required
from app.models.communique import Communique
from app.models.annee_diplomation import AnneeDiplomation
from app.models.dossier_diplomation import DossierDiplomation
from app import db
import datetime

directeur_bp = Blueprint('directeur', __name__)


def _q_dossiers_annee():
    annee = session.get('annee_active_code')
    q = DossierDiplomation.query
    if annee:
        q = q.filter(DossierDiplomation.annee_academique == annee)
    return q


@directeur_bp.route('/dashboard')
@login_required
@role_required('directeur')
def dashboard():
    annee = session.get('annee_active_code')
    q_com = Communique.query
    if annee:
        q_com = q_com.filter_by(annee_academique=annee)
    communiques = q_com.order_by(Communique.created_at.desc()).limit(5).all()
    nb_dossiers_signature = _q_dossiers_annee().filter_by(statut='SIGNATURE_DIRECTEUR').count()
    nb_dossiers_signes = _q_dossiers_annee().filter(
        DossierDiplomation.date_signature_directeur.isnot(None)
    ).count()
    # Vérifier si une procédure est déjà en cours pour l'année active
    procedure_en_cours = False
    if annee:
        from app.models.annee_diplomation import AnneeDiplomation
        annee_obj = AnneeDiplomation.query.filter_by(code=annee, processus_lance=True).first()
        procedure_en_cours = annee_obj is not None
    return render_template(
        'directeur/dashboard.html',
        communiques=communiques,
        nb_dossiers_signature=nb_dossiers_signature,
        nb_dossiers_signes=nb_dossiers_signes,
        procedure_en_cours=procedure_en_cours,
    )


@directeur_bp.route('/communiques')
@login_required
@role_required('directeur')
def liste_communiques():
    annee = session.get('annee_active_code')
    q_com = Communique.query
    if annee:
        q_com = q_com.filter_by(annee_academique=annee)
    communiques = q_com.order_by(Communique.created_at.desc()).all()
    annees = AnneeDiplomation.query.order_by(AnneeDiplomation.code.desc()).all()
    # Procédure en cours ?
    procedure_en_cours = False
    if annee:
        from app.models.annee_diplomation import AnneeDiplomation as _AD
        annee_obj = _AD.query.filter_by(code=annee, processus_lance=True).first()
        procedure_en_cours = annee_obj is not None
    return render_template('directeur/communiques.html',
                           communiques=communiques, annees=annees,
                           procedure_en_cours=procedure_en_cours)


@directeur_bp.route('/communiques/nouveau', methods=['GET', 'POST'])
@login_required
@role_required('directeur')
def nouveau_communique():
    annees_disponibles = [
        a.code for a in
        AnneeDiplomation.query.filter_by(actif=True).order_by(AnneeDiplomation.code.desc()).all()
    ]

    if request.method == 'POST':
        communique = Communique(
            numero_communique=request.form['numero_communique'],
            titre=request.form['titre'],
            contenu=request.form.get('contenu', ''),
            date_emission=datetime.date.today(),
            date_limite_depot=request.form.get('date_limite_depot') or None,
            annee_academique=request.form['annee_academique'],
            objet=request.form.get('objet', ''),
            type_processus=request.form.get('type_processus', 'DIPLOMATION'),
            statut='BROUILLON',
            id_directeur=current_user.id_directeur,
        )
        db.session.add(communique)
        db.session.commit()
        flash('Communiqué créé avec succès.', 'success')
        return redirect(url_for('directeur.liste_communiques'))

    return render_template('directeur/nouveau_communique.html',
                           annees_disponibles=annees_disponibles)


@directeur_bp.route('/communiques/<int:id>/publier', methods=['POST'])
@login_required
@role_required('directeur')
def publier_communique(id):
    communique = Communique.query.get_or_404(id)
    communique.statut = 'PUBLIE'
    db.session.commit()
    flash('Communiqué publié.', 'success')
    return redirect(url_for('directeur.liste_communiques'))


@directeur_bp.route('/communiques/<int:id>/supprimer', methods=['POST'])
@login_required
@role_required('directeur')
def supprimer_communique(id):
    communique = Communique.query.get_or_404(id)
    if communique.statut == 'PUBLIE':
        flash('Impossible de supprimer un communiqué déjà publié.', 'danger')
        return redirect(url_for('directeur.liste_communiques'))
    db.session.delete(communique)
    db.session.commit()
    flash('Communiqué supprimé.', 'success')
    return redirect(url_for('directeur.liste_communiques'))


@directeur_bp.route('/dossiers-signes')
@login_required
@role_required('directeur')
def dossiers_signes():
    annee_filtre = request.args.get('annee', session.get('annee_active_code', ''))
    annees = AnneeDiplomation.query.order_by(AnneeDiplomation.code.desc()).all()
    q = DossierDiplomation.query.filter(
        DossierDiplomation.date_signature_directeur.isnot(None)
    )
    if annee_filtre:
        q = q.filter(DossierDiplomation.annee_academique == annee_filtre)
    dossiers = q.order_by(DossierDiplomation.date_signature_directeur.desc()).all()
    return render_template('directeur/dossiers_signes.html',
                           dossiers=dossiers, annees=annees, annee_filtre=annee_filtre)


@directeur_bp.route('/annees/<int:id>/lancer-processus', methods=['POST'])
@login_required
@role_required('directeur')
def lancer_processus(id):
    annee = AnneeDiplomation.query.get_or_404(id)
    if annee.processus_lance:
        flash(f'Le processus {annee.code} est déjà lancé.', 'info')
        return redirect(url_for('directeur.liste_communiques'))

    # Vérifier qu'un communiqué PUBLIE existe pour cette année
    communique_ok = Communique.query.filter_by(
        annee_academique=annee.code,
        statut='PUBLIE',
        type_processus='DIPLOMATION',
    ).first()
    if not communique_ok:
        flash(
            f'Impossible de lancer le processus {annee.code} : '
            'aucun communiqué de diplomation publié pour cette année.',
            'danger',
        )
        return redirect(url_for('directeur.liste_communiques'))

    annee.processus_lance = True
    db.session.commit()
    flash(
        f'Processus de diplomation {annee.code} lancé. '
        'Les étudiants peuvent maintenant déposer leur dossier.',
        'success',
    )
    return redirect(url_for('directeur.liste_communiques'))


@directeur_bp.route('/dossiers-a-signer')
@login_required
@role_required('directeur')
def dossiers_a_signer():
    dossiers = _q_dossiers_annee().filter_by(statut='SIGNATURE_DIRECTEUR').all()
    return render_template('directeur/dossiers_a_signer.html', dossiers=dossiers)


@directeur_bp.route('/dossiers/<int:id>/signer', methods=['POST'])
@login_required
@role_required('directeur')
def signer_dossier(id):
    dossier = DossierDiplomation.query.get_or_404(id)
    dossier.statut = 'SIGNATURE_RECTEUR'
    dossier.date_signature_directeur = datetime.date.today()
    db.session.commit()
    flash('Diplôme signé — transmis au Recteur.', 'success')
    return redirect(url_for('directeur.dossiers_a_signer'))
