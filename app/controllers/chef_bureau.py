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

    # Enrichir avec le statut de transmission de la liste finissants
    for d in dossiers_raw:
        d._sur_liste = _est_sur_liste(d.matricule, d.annee_academique)
        fiche = ListeFinissants.query.filter_by(
            matricule=d.matricule, annee_academique=d.annee_academique
        ).first()
        d._statut_liste = fiche.statut_correction if fiche else None

    return render_template('chef_bureau/impressions.html', dossiers=dossiers_raw)


@chef_bureau_bp.route('/dossiers/<int:id>/impression-provisoire', methods=['POST'])
@login_required
@role_required('chef_bureau')
def lancer_impression_provisoire(id):
    dossier = DossierDiplomation.query.get_or_404(id)

    if not _est_sur_liste(dossier.matricule, dossier.annee_academique):
        flash(
            f'Impression impossible : {dossier.matricule} n\'est pas sur la liste officielle.',
            'danger'
        )
        return redirect(url_for('chef_bureau.impressions'))

    ancien = dossier.statut
    dossier.statut = 'IMPRESSION_PROVISOIRE'
    # Réinitialiser la conformité pour ce nouveau jet
    dossier.est_diplome_conforme = None
    _log(id, 'IMPRESSION_PROVISOIRE', ancien, 'IMPRESSION_PROVISOIRE',
         str(current_user.id_representant), 'chef_bureau')
    db.session.commit()
    flash('Premier jet lancé — les représentants peuvent maintenant vérifier les diplômes.', 'success')
    return redirect(url_for('chef_bureau.impressions'))


@chef_bureau_bp.route('/dossiers/<int:id>/corriger-et-reimprimer', methods=['POST'])
@login_required
@role_required('chef_bureau')
def corriger_et_reimprimer(id):
    """
    Applique les corrections signalées par le représentant
    et relance l'impression provisoire (nouveau jet).
    """
    dossier = DossierDiplomation.query.get_or_404(id)
    # Appliquer les corrections manuelles si fournies
    nom  = request.form.get('nom_sur_diplome', '').strip().upper()
    prenom = request.form.get('prenom_sur_diplome', '').strip()
    ddn  = request.form.get('ddn_sur_diplome', '').strip()
    lddn = request.form.get('lddn_sur_diplome', '').strip()

    if nom:    dossier.nom_sur_diplome    = nom
    if prenom: dossier.prenom_sur_diplome = prenom
    if ddn:
        try:
            import datetime as dt
            dossier.ddn_sur_diplome = dt.datetime.strptime(ddn, '%Y-%m-%d').date()
        except ValueError:
            pass
    if lddn: dossier.lddn_sur_diplome = lddn

    # Réinitialiser conformité et relancer le jet
    dossier.est_diplome_conforme = None
    dossier.observations = None
    _log(id, 'REIMPRESSON_PROVISOIRE', 'IMPRESSION_PROVISOIRE', 'IMPRESSION_PROVISOIRE',
         str(current_user.id_representant), 'chef_bureau')
    db.session.commit()
    flash(
        f'Corrections appliquées — nouveau jet lancé pour {dossier.nom_sur_diplome} {dossier.prenom_sur_diplome}.',
        'success'
    )
    return redirect(url_for('chef_bureau.impressions'))


@chef_bureau_bp.route('/production-definitive-globale', methods=['POST'])
@login_required
@role_required('chef_bureau')
def production_definitive_globale():
    """
    Passe TOUS les dossiers conformes (est_diplome_conforme=True)
    en PRODUCTION_DEFINITIVE — mise en attente des résultats définitifs.
    """
    from flask import session as flask_session
    annee = flask_session.get('annee_active_code', '')
    dossiers = _q_annee().filter(
        DossierDiplomation.statut == 'IMPRESSION_PROVISOIRE',
        DossierDiplomation.est_diplome_conforme == True
    ).all()

    if not dossiers:
        flash('Aucun dossier conforme à passer en production définitive.', 'warning')
        return redirect(url_for('chef_bureau.impressions'))

    non_conformes = _q_annee().filter(
        DossierDiplomation.statut == 'IMPRESSION_PROVISOIRE',
        DossierDiplomation.est_diplome_conforme != True
    ).count()

    if non_conformes > 0:
        flash(
            f'Impossible : {non_conformes} dossier(s) ne sont pas encore confirmés conformes '
            f'par les représentants.',
            'danger'
        )
        return redirect(url_for('chef_bureau.impressions'))

    for dossier in dossiers:
        ancien = dossier.statut
        dossier.statut = 'PRODUCTION_DEFINITIVE'
        _log(dossier.id_dossier, 'PRODUCTION_DEFINITIVE', ancien, 'PRODUCTION_DEFINITIVE',
             str(current_user.id_representant), 'chef_bureau')

    db.session.commit()
    flash(
        f'{len(dossiers)} dossier(s) passé(s) en PRODUCTION_DÉFINITIVE — '
        f'en attente des résultats officiels.',
        'success'
    )
    return redirect(url_for('chef_bureau.impressions'))


@chef_bureau_bp.route('/dossiers/<int:id>/production-definitive', methods=['POST'])
@login_required
@role_required('chef_bureau')
def production_definitive(id):
    dossier = DossierDiplomation.query.get_or_404(id)
    ancien = dossier.statut
    dossier.statut = 'PRODUCTION_DEFINITIVE'
    _log(id, 'PRODUCTION_DEFINITIVE', ancien, 'PRODUCTION_DEFINITIVE',
         str(current_user.id_representant), 'chef_bureau')
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
