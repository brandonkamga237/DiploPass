import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from app.utils.decorators import role_required
from app.models.dossier_diplomation import DossierDiplomation
from app.models.dossier_formalisation import DossierFormalisation
from app.models.document_requis import DocumentRequis
from app.models.piece_jointe import PieceJointe
from app.models.communique import Communique
from app.models.representant import RepresentantFiliere
from app.models.historique_phases import HistoriquePhases
from app import db
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

EXTENSIONS_AUTORISEES = {'pdf', 'jpg', 'jpeg', 'png'}
TAILLE_MAX_OCTETS = 10 * 1024 * 1024  # 10 Mo

def _ext_ok(nom_fichier: str) -> bool:
    return '.' in nom_fichier and nom_fichier.rsplit('.', 1)[1].lower() in EXTENSIONS_AUTORISEES

etudiant_bp = Blueprint('etudiant', __name__)


def _processus_actif_pour_etudiant(etudiant):
    """
    Retourne l'AnneeDiplomation active et lancée correspondant à l'étudiant, ou None.
    Un étudiant ne peut soumettre que si le processus est explicitement lancé
    par le Directeur pour son année académique.
    """
    from app.models.annee_diplomation import AnneeDiplomation
    if not etudiant.annee_academique:
        return None
    return AnneeDiplomation.query.filter_by(
        code=etudiant.annee_academique,
        actif=True,
        processus_lance=True,
    ).first()


def _communique_pour_etudiant(etudiant):
    """Retourne le communiqué PUBLIE de l'année de l'étudiant, ou None."""
    today = datetime.date.today()
    if not etudiant.annee_academique:
        return None
    return (Communique.query
            .filter(
                Communique.statut == 'PUBLIE',
                Communique.type_processus == 'DIPLOMATION',
                Communique.annee_academique == etudiant.annee_academique,
                db.or_(Communique.date_limite_depot.is_(None),
                       Communique.date_limite_depot >= today),
            )
            .order_by(Communique.date_emission.desc())
            .first())


def _representant_pour_filiere(filiere):
    """Retourne le représentant actif dont la filière correspond, ou None."""
    return RepresentantFiliere.query.filter_by(
        filiere_geree=filiere, actif=True
    ).first()


# ── Dashboard ─────────────────────────────────────────────────────────────────

@etudiant_bp.route('/dashboard')
@login_required
@role_required('etudiant')
def dashboard():
    dossier = current_user.dossier_diplomation
    processus = _processus_actif_pour_etudiant(current_user)
    communique = _communique_pour_etudiant(current_user) if processus else None

    # Étudiant d'une année passée dont le dossier est clôturé → vue résultats
    est_ancien_diplome = (
        dossier is not None
        and dossier.statut == 'CLOTURE'
        and processus is None
    )
    return render_template(
        'etudiant/dashboard.html',
        communique=communique,
        dossier=dossier,
        processus=processus,
        est_ancien_diplome=est_ancien_diplome,
    )


# ── Soumission du dossier de diplomation ─────────────────────────────────────

@etudiant_bp.route('/soumettre-dossier', methods=['GET', 'POST'])
@login_required
@role_required('etudiant')
def soumettre_dossier():
    if not _processus_actif_pour_etudiant(current_user):
        flash('Le processus de diplomation n\'est pas encore ouvert pour votre année.', 'warning')
        return redirect(url_for('etudiant.dashboard'))

    communique = _communique_pour_etudiant(current_user)
    if not communique:
        flash('Aucun communiqué publié pour votre année de diplomation.', 'warning')
        return redirect(url_for('etudiant.dashboard'))

    if current_user.dossier_diplomation:
        flash('Vous avez déjà soumis un dossier de diplomation.', 'info')
        return redirect(url_for('etudiant.detail_dossier'))

    documents = DocumentRequis.query.order_by(DocumentRequis.numero).all()

    if request.method == 'POST':
        from app.services import storage_service as storage

        representant = _representant_pour_filiere(current_user.filiere)

        dossier = DossierDiplomation(
            matricule=current_user.matricule,
            statut='DEPOSE',
            annee_academique=communique.annee_academique,
            date_limite_depot=communique.date_limite_depot,
            id_communique=communique.id_communique,
            id_representant=representant.id_representant if representant else None,
        )
        db.session.add(dossier)
        db.session.flush()

        db.session.add(HistoriquePhases(
            id_dossier=dossier.id_dossier,
            phase='DEPOT',
            ancien_statut=None,
            nouveau_statut='DEPOSE',
            id_acteur=current_user.matricule,
            role_acteur='etudiant',
            date_action=datetime.datetime.now(),
        ))

        # Upload des fichiers fournis à la soumission
        nb_uploads = 0
        erreurs = []
        for doc in documents:
            fichier = request.files.get(f'fichier_{doc.id_document}')
            if not fichier or fichier.filename == '':
                continue
            if not _ext_ok(fichier.filename):
                erreurs.append(f'{doc.nom} : format non autorisé (PDF/JPG/PNG uniquement).')
                continue
            fichier.seek(0, 2)
            if fichier.tell() > TAILLE_MAX_OCTETS:
                erreurs.append(f'{doc.nom} : fichier trop volumineux (max 10 Mo).')
                continue
            fichier.seek(0)
            try:
                cle, taille = storage.upload_piece(
                    fichier, dossier.id_dossier,
                    doc.id_document,
                    secure_filename(fichier.filename),
                    fichier.content_type or 'application/octet-stream',
                )
                db.session.add(PieceJointe(
                    id_dossier=dossier.id_dossier,
                    id_document_requis=doc.id_document,
                    nom_original=secure_filename(fichier.filename),
                    cle_minio=cle,
                    mime_type=fichier.content_type or 'application/octet-stream',
                    taille_octets=taille,
                    statut='DEPOSE',
                ))
                nb_uploads += 1
            except Exception as e:
                erreurs.append(f'{doc.nom} : erreur upload ({e}).')

        db.session.commit()

        for err in erreurs:
            flash(err, 'warning')

        if nb_uploads:
            flash(f'Dossier créé — {nb_uploads} pièce(s) téléversée(s). Vous pouvez compléter les pièces manquantes depuis votre dossier.', 'success')
        else:
            flash('Dossier créé. Déposez maintenant vos pièces justificatives.', 'info')

        return redirect(url_for('etudiant.detail_dossier'))

    return render_template(
        'etudiant/soumettre_dossier.html',
        communique=communique,
        documents=documents,
    )


# ── Détail du dossier ─────────────────────────────────────────────────────────

@etudiant_bp.route('/dossier')
@login_required
@role_required('etudiant')
def detail_dossier():
    dossier = current_user.dossier_diplomation
    if not dossier:
        flash('Vous n\'avez pas encore soumis de dossier.', 'info')
        return redirect(url_for('etudiant.dashboard'))
    documents   = DocumentRequis.query.order_by(DocumentRequis.numero).all()
    # index des pièces déjà déposées : id_document_requis → PieceJointe
    pieces_map  = {p.id_document_requis: p for p in dossier.pieces_jointes}
    return render_template(
        'etudiant/detail_dossier.html',
        dossier=dossier,
        documents=documents,
        pieces_map=pieces_map,
    )


# ── Upload d'une pièce justificative ─────────────────────────────────────────

@etudiant_bp.route('/dossier/pieces/<int:id_document>/upload', methods=['POST'])
@login_required
@role_required('etudiant')
def upload_piece(id_document):
    from app.services import storage_service as storage
    dossier = current_user.dossier_diplomation
    if not dossier:
        abort(404)
    if dossier.statut not in ('DEPOSE', 'INCOMPLET'):
        flash('Votre dossier n\'est plus modifiable à ce stade.', 'warning')
        return redirect(url_for('etudiant.detail_dossier'))

    fichier = request.files.get('fichier')
    if not fichier or fichier.filename == '':
        flash('Aucun fichier sélectionné.', 'warning')
        return redirect(url_for('etudiant.detail_dossier'))

    if not _ext_ok(fichier.filename):
        flash('Format non autorisé. Utilisez PDF, JPG ou PNG.', 'danger')
        return redirect(url_for('etudiant.detail_dossier'))

    fichier.seek(0, 2)
    if fichier.tell() > TAILLE_MAX_OCTETS:
        flash('Fichier trop volumineux (max 10 Mo).', 'danger')
        return redirect(url_for('etudiant.detail_dossier'))
    fichier.seek(0)

    nom_original = secure_filename(fichier.filename)
    mime_type    = fichier.content_type or 'application/octet-stream'

    # Supprimer l'ancienne pièce pour ce document si elle existe
    ancienne = PieceJointe.query.filter_by(
        id_dossier=dossier.id_dossier,
        id_document_requis=id_document,
    ).first()
    if ancienne:
        storage.supprimer(ancienne.cle_minio)
        db.session.delete(ancienne)
        db.session.flush()

    try:
        cle, taille = storage.upload_piece(
            fichier, dossier.id_dossier, id_document, nom_original, mime_type
        )
    except Exception as e:
        flash(f'Erreur lors de l\'upload : {e}', 'danger')
        return redirect(url_for('etudiant.detail_dossier'))

    piece = PieceJointe(
        id_dossier=dossier.id_dossier,
        id_document_requis=id_document,
        nom_original=nom_original,
        cle_minio=cle,
        mime_type=mime_type,
        taille_octets=taille,
        statut='DEPOSE',
    )
    db.session.add(piece)
    db.session.commit()
    flash('Pièce déposée avec succès.', 'success')
    return redirect(url_for('etudiant.detail_dossier'))


# ── Suppression d'une pièce ───────────────────────────────────────────────────

@etudiant_bp.route('/dossier/pieces/<int:id_piece>/supprimer', methods=['POST'])
@login_required
@role_required('etudiant')
def supprimer_piece(id_piece):
    from app.services import storage_service as storage
    piece = PieceJointe.query.get_or_404(id_piece)
    dossier = current_user.dossier_diplomation
    if not dossier or piece.id_dossier != dossier.id_dossier:
        abort(403)
    if dossier.statut not in ('DEPOSE', 'INCOMPLET'):
        flash('Votre dossier n\'est plus modifiable à ce stade.', 'warning')
        return redirect(url_for('etudiant.detail_dossier'))
    storage.supprimer(piece.cle_minio)
    db.session.delete(piece)
    db.session.commit()
    flash('Pièce supprimée.', 'info')
    return redirect(url_for('etudiant.detail_dossier'))


# ── Voir / télécharger une pièce (URL signée MinIO) ──────────────────────────

@etudiant_bp.route('/dossier/pieces/<int:id_piece>/voir')
@login_required
@role_required('etudiant')
def voir_piece(id_piece):
    from app.services import storage_service as storage
    piece = PieceJointe.query.get_or_404(id_piece)
    dossier = current_user.dossier_diplomation
    if not dossier or piece.id_dossier != dossier.id_dossier:
        abort(403)
    try:
        url = storage.presigned_url(piece.cle_minio, expires_sec=1800)
        return redirect(url)
    except Exception:
        abort(500)


# ── Profil & mot de passe ─────────────────────────────────────────────────────

@etudiant_bp.route('/profil')
@login_required
@role_required('etudiant')
def profil():
    return render_template('etudiant/profil.html')


@etudiant_bp.route('/changer-mot-de-passe', methods=['GET', 'POST'])
@login_required
@role_required('etudiant')
def changer_mot_de_passe():
    if request.method == 'POST':
        ancien = request.form.get('ancien_mot_de_passe', '')
        nouveau = request.form.get('nouveau_mot_de_passe', '')
        confirmation = request.form.get('confirmation', '')

        if not current_user.check_password(ancien):
            flash('Ancien mot de passe incorrect.', 'danger')
        elif nouveau != confirmation:
            flash('Les mots de passe ne correspondent pas.', 'danger')
        elif len(nouveau) < 6:
            flash('Le mot de passe doit contenir au moins 6 caractères.', 'warning')
        else:
            current_user.set_password(nouveau)
            db.session.commit()
            flash('Mot de passe modifié avec succès.', 'success')
            return redirect(url_for('etudiant.profil'))

    return render_template('etudiant/changer_mot_de_passe.html')
