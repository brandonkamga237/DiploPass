from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_required, current_user
from app.utils.decorators import role_required
from app.models.dossier_diplomation import DossierDiplomation
from app.models.historique_phases import HistoriquePhases
from app.models.liste_finissants import ListeFinissants
from app import db
import datetime

chef_bureau_bp = Blueprint('chef_bureau', __name__)


def _q_annee():
    """Base query filtré par l'année académique active."""
    annee = session.get('annee_active_code')
    q = DossierDiplomation.query
    if annee:
        q = q.filter(DossierDiplomation.annee_academique == annee)
    return q


@chef_bureau_bp.route('/dashboard')
@login_required
@role_required('chef_bureau')
def dashboard():
    q = _q_annee()
    stats = {
        'a_authentifier':   q.filter_by(statut='EN_VERIFICATION').count(),
        'authentifies':     q.filter_by(statut='AUTHENTIFICATION').count(),
        'liste_finissants': q.filter_by(statut='LISTE_FINISSANTS').count(),
        'imp_provisoire':   q.filter_by(statut='IMPRESSION_PROVISOIRE').count(),
        'prod_definitive':  q.filter_by(statut='PRODUCTION_DEFINITIVE').count(),
        'a_signer':         q.filter_by(statut='SIGNATURE_DIRECTEUR').count(),
    }
    return render_template('chef_bureau/dashboard.html', stats=stats)


@chef_bureau_bp.route('/authentification')
@login_required
@role_required('chef_bureau')
def dossiers_authentification():
    dossiers = _q_annee().filter_by(statut='EN_VERIFICATION').all()
    return render_template('chef_bureau/authentification.html', dossiers=dossiers)


@chef_bureau_bp.route('/dossiers/<int:id>/authentifier', methods=['POST'])
@login_required
@role_required('chef_bureau')
def authentifier(id):
    dossier = DossierDiplomation.query.get_or_404(id)
    resultat = request.form.get('resultat')
    ancien = dossier.statut

    if resultat == 'AUTHENTIQUE':
        dossier.statut = 'AUTHENTIFICATION'
        dossier.resultat_authentification = 'AUTHENTIQUE'
        nouveau = 'AUTHENTIFICATION'
    else:
        dossier.statut = 'AUTH_REJETEE'
        dossier.resultat_authentification = 'FAUX'
        dossier.motif_rejet = request.form.get('motif', 'Diplôme non authentique')
        nouveau = 'AUTH_REJETEE'

    _log(id, 'AUTHENTIFICATION', ancien, nouveau, current_user.id_representant, 'chef_bureau')
    db.session.commit()
    flash(f'Résultat enregistré : {resultat}.', 'success')
    return redirect(url_for('chef_bureau.dossiers_authentification'))


def _est_sur_liste(matricule, annee_academique):
    """Vérifie si un étudiant est validé sur la liste officielle des finissants."""
    return ListeFinissants.query.filter_by(
        matricule=matricule,
        annee_academique=annee_academique,
        valide=True
    ).first() is not None


@chef_bureau_bp.route('/impressions')
@login_required
@role_required('chef_bureau')
def impressions():
    from flask_login import current_user
    annee = _q_annee()
    dossiers_raw = annee.filter(
        DossierDiplomation.statut.in_(['AUTHENTIFICATION', 'LISTE_FINISSANTS', 'IMPRESSION_PROVISOIRE'])
    ).all()

    # Enrichir chaque dossier avec info liste finissants
    for d in dossiers_raw:
        d._sur_liste = _est_sur_liste(d.matricule, d.annee_academique)

    return render_template('chef_bureau/impressions.html', dossiers=dossiers_raw)


@chef_bureau_bp.route('/dossiers/<int:id>/impression-provisoire', methods=['POST'])
@login_required
@role_required('chef_bureau')
def lancer_impression_provisoire(id):
    dossier = DossierDiplomation.query.get_or_404(id)

    # Vérifier que l'étudiant est sur la liste des finissants
    if not _est_sur_liste(dossier.matricule, dossier.annee_academique):
        flash(
            f'Impression impossible : {dossier.matricule} n\'est pas sur la liste '
            f'officielle des finissants validés pour {dossier.annee_academique}.',
            'danger'
        )
        return redirect(url_for('chef_bureau.impressions'))

    ancien = dossier.statut
    dossier.statut = 'IMPRESSION_PROVISOIRE'
    _log(id, 'IMPRESSION_PROVISOIRE', ancien, 'IMPRESSION_PROVISOIRE',
         current_user.id_representant, 'chef_bureau')
    db.session.commit()
    flash('Impression provisoire lancée.', 'success')
    return redirect(url_for('chef_bureau.impressions'))


@chef_bureau_bp.route('/dossiers/<int:id>/production-definitive', methods=['POST'])
@login_required
@role_required('chef_bureau')
def production_definitive(id):
    dossier = DossierDiplomation.query.get_or_404(id)
    ancien = dossier.statut
    dossier.statut = 'PRODUCTION_DEFINITIVE'
    _log(id, 'PRODUCTION_DEFINITIVE', ancien, 'PRODUCTION_DEFINITIVE',
         current_user.id_representant, 'chef_bureau')
    db.session.commit()
    flash('Production définitive enregistrée.', 'success')
    return redirect(url_for('chef_bureau.impressions'))


@chef_bureau_bp.route('/dossiers/<int:id>/envoyer-directeur', methods=['POST'])
@login_required
@role_required('chef_bureau')
def envoyer_directeur(id):
    dossier = DossierDiplomation.query.get_or_404(id)
    ancien = dossier.statut
    dossier.statut = 'SIGNATURE_DIRECTEUR'
    _log(id, 'SIGNATURE_DIRECTEUR', ancien, 'SIGNATURE_DIRECTEUR',
         current_user.id_representant, 'chef_bureau')
    db.session.commit()
    flash('Dossier envoyé au Directeur pour signature.', 'success')
    return redirect(url_for('chef_bureau.impressions'))


@chef_bureau_bp.route('/dossiers/<int:id>/diplome')
@login_required
@role_required('chef_bureau')
def apercu_diplome(id):
    from app.models.etudiant import Etudiant
    from app.models.filiere import Filiere
    dossier = DossierDiplomation.query.get_or_404(id)
    etudiant = Etudiant.query.get_or_404(dossier.matricule)
    filiere = Filiere.query.filter_by(code=etudiant.filiere).first()
    if filiere:
        etudiant.filiere_obj = filiere
    return render_template(
        'documents/diplome.html',
        dossier=dossier,
        etudiant=etudiant,
        recteur_nom='',
        ministre_nom='Jacques Fame Ndongo',
    )


def _log(id_dossier, phase, ancien, nouveau, id_acteur, role):
    h = HistoriquePhases(
        id_dossier=id_dossier,
        phase=phase,
        ancien_statut=ancien,
        nouveau_statut=nouveau,
        id_acteur=id_acteur,
        role_acteur=role,
        date_action=datetime.datetime.now(),
    )
    db.session.add(h)
