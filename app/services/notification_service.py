from app import db


def notifier_etudiant(matricule, message, type_notif='INFO'):
    """Placeholder pour les notifications futures (email, SMS)."""
    print(f'[NOTIF] {type_notif} → {matricule}: {message}')
