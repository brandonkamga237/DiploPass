from flask import Blueprint, render_template, request, flash, redirect, url_for, session, abort
from flask_login import login_required, current_user
from app.utils.decorators import role_required
from app.models.dossier_diplomation import DossierDiplomation
from app.models.dossier_formalisation import DossierFormalisation
from app.models.document_requis import DocumentRequis
from app.models.piece_jointe import PieceJointe
from app.models.etudiant import Etudiant
from app.models.historique_phases import HistoriquePhases
from app import db
import datetime

representant_bp = Blueprint('representant', __name__)


def _dossiers_filiere():
    """Dossiers de la filière du représentant pour l'année académique active."""
    annee = session.get('annee_active_code')
    q = (
        DossierDiplomation.query
        .join(Etudiant, DossierDiplomation.matricule == Etudiant.matricule)
        .filter(Etudiant.filiere == current_user.filiere_geree)
    )
    if annee:
        q = q.filter(DossierDiplomation.annee_academique == annee)
    return q


@representant_bp.route('/dashboard')
@login_required
@role_required('representant', 'chef_bureau')
def dashboard():
    annee = session.get('annee_active_code')
    dossiers = _dossiers_filiere().order_by(DossierDiplomation.date_depot.desc()).all()

    nb_etudiants = (
        Etudiant.query
        .filter_by(filiere=current_user.filiere_geree, annee_academique=annee)
        .count() if annee else
        Etudiant.query.filter_by(filiere=current_user.filiere_geree).count()
    )

    STATUTS_AVANCES = ['EN_VERIFICATION', 'AUTHENTIFICATION', 'LISTE_FINISSANTS',
                       'IMPRESSION_PROVISOIRE', 'PRODUCTION_DEFINITIVE',
                       'SIGNATURE_DIRECTEUR', 'SIGNATURE_RECTEUR',
                       'SIGNATURE_MINISTRE', 'FORMALISATION', 'CLOTURE']
    stats = {
        'total':              len(dossiers),
        'deposes':            sum(1 for d in dossiers if d.statut == 'DEPOSE'),
        'en_verification':    sum(1 for d in dossiers if d.statut == 'EN_VERIFICATION'),
        'incomplets':         sum(1 for d in dossiers if d.statut == 'INCOMPLET'),
        'a_authentifier':     sum(1 for d in dossiers if d.statut == 'EN_VERIFICATION'),
        'authentifies':       sum(1 for d in dossiers if d.statut == 'AUTHENTIFICATION'),
        'valides':            sum(1 for d in dossiers if d.statut in STATUTS_AVANCES),
        'clotures':           sum(1 for d in dossiers if d.statut == 'CLOTURE'),
    }
    return render_template(
        'representant/dashboard.html',
        dossiers=dossiers[:10],
        stats=stats,
        nb_etudiants=nb_etudiants,
        filiere=current_user.filiere_geree,
    )


@representant_bp.route('/dossiers')
@login_required
@role_required('representant', 'chef_bureau')
def liste_dossiers():
    statut = request.args.get('statut', '')
    q = _dossiers_filiere()
    if statut:
        q = q.filter(DossierDiplomation.statut == statut)
    dossiers = q.order_by(DossierDiplomation.date_depot.desc()).all()
    return render_template('representant/dossiers.html', dossiers=dossiers, statut_filtre=statut)


@representant_bp.route('/dossiers/<int:id>')
@login_required
@role_required('representant', 'chef_bureau')
def detail_dossier(id):
    dossier   = DossierDiplomation.query.get_or_404(id)
    documents = DocumentRequis.query.order_by(DocumentRequis.numero).all()
    pieces_map = {p.id_document_requis: p for p in dossier.pieces_jointes}
    return render_template(
        'representant/detail_dossier.html',
        dossier=dossier,
        documents=documents,
        pieces_map=pieces_map,
    )


@representant_bp.route('/dossiers/<int:id_dossier>/pieces/<int:id_piece>/voir')
@login_required
@role_required('representant', 'chef_bureau')
def voir_piece(id_dossier, id_piece):
    from app.services import storage_service as storage
    piece = PieceJointe.query.get_or_404(id_piece)
    if piece.id_dossier != id_dossier:
        abort(403)
    try:
        url = storage.presigned_url(piece.cle_minio, expires_sec=1800)
        return redirect(url)
    except Exception:
        abort(500)


@representant_bp.route('/dossiers/<int:id>/verifier', methods=['POST'])
@login_required
@role_required('representant', 'chef_bureau')
def verifier_dossier(id):
    dossier = DossierDiplomation.query.get_or_404(id)
    ancien = dossier.statut
    complet = request.form.get('complet') == '1'

    if complet:
        dossier.statut = 'EN_VERIFICATION'
        nouveau = 'EN_VERIFICATION'
    else:
        dossier.statut = 'INCOMPLET'
        nouveau = 'INCOMPLET'
        dossier.observations = request.form.get('observations', '')

    _log(id, 'VERIFICATION', ancien, nouveau, current_user.id_representant, 'representant')
    db.session.commit()
    flash('Statut mis à jour.', 'success')
    return redirect(url_for('representant.detail_dossier', id=id))


@representant_bp.route('/authentification')
@login_required
@role_required('representant', 'chef_bureau')
def liste_authentification():
    """Dossiers en attente d'authentification pour la filière du représentant."""
    dossiers = _dossiers_filiere().filter(
        DossierDiplomation.statut == 'EN_VERIFICATION'
    ).order_by(DossierDiplomation.date_depot).all()
    return render_template('representant/authentification.html', dossiers=dossiers)


@representant_bp.route('/dossiers/<int:id>/authentifier', methods=['POST'])
@login_required
@role_required('representant', 'chef_bureau')
def authentifier(id):
    dossier = DossierDiplomation.query.get_or_404(id)
    ancien  = dossier.statut
    resultat = request.form.get('resultat')

    if resultat == 'AUTHENTIQUE':
        dossier.statut                    = 'AUTHENTIFICATION'
        dossier.resultat_authentification = 'AUTHENTIQUE'
        nouveau = 'AUTHENTIFICATION'
        flash('Diplôme authentifié — dossier validé.', 'success')
    else:
        dossier.statut                    = 'AUTH_REJETEE'
        dossier.resultat_authentification = 'FAUX'
        dossier.observations              = request.form.get('motif', '')
        nouveau = 'AUTH_REJETEE'
        flash('Diplôme rejeté — dossier marqué comme non authentique.', 'danger')

    _log(id, 'AUTHENTIFICATION', ancien, nouveau,
         str(current_user.id_representant), 'representant')
    db.session.commit()
    return redirect(url_for('representant.liste_authentification'))


@representant_bp.route('/dossiers/<int:id>/corriger', methods=['POST'])
@login_required
@role_required('representant', 'chef_bureau')
def corriger_dossier(id):
    dossier = DossierDiplomation.query.get_or_404(id)
    dossier.nom_sur_diplome = request.form.get('nom_sur_diplome', dossier.nom_sur_diplome)
    dossier.prenom_sur_diplome = request.form.get('prenom_sur_diplome', dossier.prenom_sur_diplome)
    dossier.ddn_sur_diplome = request.form.get('ddn_sur_diplome') or dossier.ddn_sur_diplome
    dossier.lddn_sur_diplome = request.form.get('lddn_sur_diplome', dossier.lddn_sur_diplome)
    db.session.commit()
    flash('Informations corrigées.', 'success')
    return redirect(url_for('representant.detail_dossier', id=id))


@representant_bp.route('/dossiers/<int:id>/confirmer-liste', methods=['POST'])
@login_required
@role_required('representant', 'chef_bureau')
def confirmer_liste(id):
    dossier = DossierDiplomation.query.get_or_404(id)
    ancien = dossier.statut
    dossier.statut = 'LISTE_FINISSANTS'
    _log(id, 'LISTE_FINISSANTS', ancien, 'LISTE_FINISSANTS',
         current_user.id_representant, 'representant')
    db.session.commit()
    flash('Étudiant confirmé sur la liste des finissants.', 'success')
    return redirect(url_for('representant.detail_dossier', id=id))


@representant_bp.route('/dossiers/<int:id>/formalisation', methods=['GET', 'POST'])
@login_required
@role_required('representant', 'chef_bureau')
def formalisation(id):
    dossier = DossierDiplomation.query.get_or_404(id)
    if request.method == 'POST':
        if not dossier.formalisation:
            f = DossierFormalisation(
                id_dossier=dossier.id_dossier,
                matricule=dossier.matricule,
                annee_academique=dossier.annee_academique,
            )
            db.session.add(f)
            db.session.flush()
        else:
            f = dossier.formalisation

        f.recu_quitus_cycle = bool(request.form.get('recu_quitus_cycle'))
        f.quitus_non_redevance = bool(request.form.get('quitus_non_redevance'))
        f.attestation_depot_memoire = bool(request.form.get('attestation_depot_memoire'))
        f.recu_association_etudiants = bool(request.form.get('recu_association_etudiants'))
        f.photocopie_cni = bool(request.form.get('photocopie_cni'))
        f.photocopie_badge_etudiant = bool(request.form.get('photocopie_badge_etudiant'))
        f.quitus_bibliotheque = bool(request.form.get('quitus_bibliotheque'))

        pieces = [
            f.recu_quitus_cycle, f.quitus_non_redevance,
            f.attestation_depot_memoire, f.recu_association_etudiants,
            f.photocopie_cni, f.photocopie_badge_etudiant, f.quitus_bibliotheque,
        ]
        f.statut = 'VALIDE' if all(pieces) else 'INCOMPLET'

        if f.statut == 'VALIDE':
            dossier.statut = 'FORMALISATION'
            _log(id, 'FORMALISATION', dossier.statut, 'FORMALISATION',
                 current_user.id_representant, 'representant')

        db.session.commit()
        flash('Dossier de formalisation mis à jour.', 'success')
        return redirect(url_for('representant.detail_dossier', id=id))

    return render_template('representant/formalisation.html', dossier=dossier)


@representant_bp.route('/dossiers/<int:id>/cloturer', methods=['POST'])
@login_required
@role_required('representant', 'chef_bureau')
def cloturer(id):
    dossier = DossierDiplomation.query.get_or_404(id)
    ancien = dossier.statut
    dossier.statut = 'CLOTURE'
    dossier.signature_empreinte_registre = bool(request.form.get('signature_registre'))
    dossier.toge_remise = bool(request.form.get('toge_remise'))
    dossier.journal_promo_remis = bool(request.form.get('journal_promo_remis'))
    _log(id, 'CLOTURE', ancien, 'CLOTURE', current_user.id_representant, 'representant')
    db.session.commit()
    flash('Dossier clôturé — diplôme remis.', 'success')
    return redirect(url_for('representant.liste_dossiers'))


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
