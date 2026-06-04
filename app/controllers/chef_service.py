from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_required
from app.utils.decorators import role_required
from app.models.dossier_diplomation import DossierDiplomation
from app.models.etudiant import Etudiant
from app.models.liste_finissants import ListeFinissants
from app.models.annee_diplomation import AnneeDiplomation
from app.models.historique_phases import HistoriquePhases
from app import db
import datetime

chef_service_bp = Blueprint('chef_service', __name__)


def _q_annee():
    """Base query filtré par l'année académique active."""
    annee = session.get('annee_active_code')
    q = DossierDiplomation.query
    if annee:
        q = q.filter(DossierDiplomation.annee_academique == annee)
    return q


@chef_service_bp.route('/dashboard')
@login_required
@role_required('chef_service')
def dashboard():
    stats = {}
    statuts = [
        'DEPOSE', 'EN_VERIFICATION', 'AUTHENTIFICATION',
        'LISTE_FINISSANTS', 'IMPRESSION_PROVISOIRE',
        'PRODUCTION_DEFINITIVE', 'SIGNATURE_DIRECTEUR',
        'SIGNATURE_RECTEUR', 'SIGNATURE_MINISTRE',
        'FORMALISATION', 'CLOTURE', 'REJETE',
    ]
    for s in statuts:
        stats[s] = _q_annee().filter_by(statut=s).count()
    total = _q_annee().count()
    return render_template('chef_service/dashboard.html', stats=stats, total=total)


@chef_service_bp.route('/dossiers')
@login_required
@role_required('chef_service')
def tous_dossiers():
    statut = request.args.get('statut', '')
    q = _q_annee()
    if statut:
        q = q.filter_by(statut=statut)
    dossiers = q.order_by(DossierDiplomation.updated_at.desc()).all()
    return render_template('chef_service/dossiers.html', dossiers=dossiers, statut_filtre=statut)


@chef_service_bp.route('/dossiers/<int:id>/passer-signature-recteur', methods=['POST'])
@login_required
@role_required('chef_service')
def passer_signature_recteur(id):
    dossier = DossierDiplomation.query.get_or_404(id)
    ancien = dossier.statut
    dossier.statut = 'SIGNATURE_RECTEUR'
    dossier.date_signature_recteur = datetime.date.today()
    _log(dossier.id_dossier, 'SIGNATURE_RECTEUR', ancien, 'SIGNATURE_RECTEUR', 'chef_service')
    db.session.commit()
    flash('Dossier transmis au Recteur.', 'success')
    return redirect(url_for('chef_service.tous_dossiers'))


@chef_service_bp.route('/dossiers/<int:id>/passer-signature-ministre', methods=['POST'])
@login_required
@role_required('chef_service')
def passer_signature_ministre(id):
    dossier = DossierDiplomation.query.get_or_404(id)
    ancien = dossier.statut
    dossier.statut = 'SIGNATURE_MINISTRE'
    dossier.date_signature_ministre = datetime.date.today()
    _log(dossier.id_dossier, 'SIGNATURE_MINISTRE', ancien, 'SIGNATURE_MINISTRE', 'chef_service')
    db.session.commit()
    flash('Dossier transmis au Ministre.', 'success')
    return redirect(url_for('chef_service.tous_dossiers'))


@chef_service_bp.route('/eligibilite')
@login_required
@role_required('chef_service')
def comparaison_eligibilite():
    """
    Vue de comparaison : tous les dossiers vs liste des finissants.
    Montre qui est éligible (sur la liste) et qui ne l'est pas.
    """
    annee = session.get('annee_active_code', '')
    annee_obj = AnneeDiplomation.query.filter_by(code=annee).first() if annee else None
    liste_finalisee = annee_obj.liste_finalisee if annee_obj else False

    # Dossiers soumis (tous statuts sauf CLOTURE)
    dossiers = _q_annee().order_by(DossierDiplomation.statut).all()

    # Matricules sur la liste validée
    matricules_valides = {
        f.matricule for f in
        ListeFinissants.query.filter_by(annee_academique=annee, valide=True).all()
    } if annee else set()

    nb_liste = len(matricules_valides)
    nb_non_eligible = sum(1 for d in dossiers if d.statut == 'NON_ELIGIBLE')
    nb_eligible = sum(1 for d in dossiers if d.statut == 'LISTE_FINISSANTS')

    return render_template(
        'chef_service/eligibilite.html',
        dossiers=dossiers,
        matricules_valides=matricules_valides,
        annee=annee,
        liste_finalisee=liste_finalisee,
        nb_liste=nb_liste,
        nb_eligible=nb_eligible,
        nb_non_eligible=nb_non_eligible,
    )


def _log(id_dossier, phase, ancien, nouveau, role):
    h = HistoriquePhases(
        id_dossier=id_dossier,
        phase=phase,
        ancien_statut=ancien,
        nouveau_statut=nouveau,
        role_acteur=role,
        date_action=datetime.datetime.now(),
    )
    db.session.add(h)
