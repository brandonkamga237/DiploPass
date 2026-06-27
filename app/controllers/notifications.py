from flask import Blueprint, render_template, redirect, url_for, session, request
from flask_login import login_required, current_user
from app.models.notification import Notification
from app import db

notif_bp = Blueprint('notifications', __name__)

ROLES_AUTORISES = ('directeur', 'chef_service', 'chef_bureau', 'representant', 'admin')


@notif_bp.route('/')
@login_required
def liste():
    role = session.get('role', '')
    if role not in ROLES_AUTORISES:
        return redirect(url_for('auth.index'))
    notifs = (
        Notification.query
        .filter_by(destinataire_type=role)
        .order_by(Notification.created_at.desc())
        .limit(50).all()
    )
    # Marquer toutes comme lues
    Notification.query.filter_by(destinataire_type=role, lue=False).update({'lue': True})
    db.session.commit()
    return render_template('notifications/liste.html', notifs=notifs)


@notif_bp.route('/<int:id>/lire', methods=['POST'])
@login_required
def marquer_lue(id):
    role = session.get('role', '')
    n = Notification.query.get_or_404(id)
    if n.destinataire_type == role:
        n.lue = True
        db.session.commit()
    next_url = request.referrer or url_for('notifications.liste')
    return redirect(next_url)
