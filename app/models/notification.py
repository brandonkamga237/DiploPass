from app import db
import datetime


class Notification(db.Model):
    __tablename__ = 'notification'

    id = db.Column(db.Integer, primary_key=True)
    # Rôle cible : 'directeur','chef_service','chef_bureau','representant','admin'
    destinataire_type = db.Column(db.String(30), nullable=False)
    # ID spécifique du destinataire (None = diffusion à tous les acteurs du type)
    destinataire_id = db.Column(db.Integer, nullable=True)
    # Filière (pour cibler le représentant / chef_bureau d'une filière spécifique)
    filiere = db.Column(db.String(100), nullable=True)
    message = db.Column(db.Text, nullable=False)
    lue = db.Column(db.Boolean, default=False)
    type_notif = db.Column(db.String(20), default='info')  # 'info', 'success', 'warning'
    lien = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<Notification [{self.destinataire_type}] {self.message[:40]}>'


def creer_notification(destinataire_type, message, type_notif='info', lien=None,
                        destinataire_id=None, filiere=None):
    """Helper : crée une notification et l'ajoute à la session (sans commit)."""
    n = Notification(
        destinataire_type=destinataire_type,
        destinataire_id=destinataire_id,
        filiere=filiere,
        message=message,
        type_notif=type_notif,
        lien=lien,
    )
    db.session.add(n)
    return n


def notifier_tous(message, type_notif='info', lien=None, roles=None):
    """Crée une notification pour chaque rôle de la liste (sans commit)."""
    if roles is None:
        roles = ['directeur', 'chef_service', 'chef_bureau', 'representant']
    for role in roles:
        creer_notification(role, message, type_notif=type_notif, lien=lien)
