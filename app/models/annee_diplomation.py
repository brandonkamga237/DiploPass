from app import db


class AnneeDiplomation(db.Model):
    """
    Année académique de diplomation — unité d'organisation d'une session.
    Chaque étudiant finissant (y compris redoublants) est rattaché à l'année
    pour laquelle il est importé. Deux sessions distinctes = deux années distinctes.
    """
    __tablename__ = 'annee_diplomation'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(9), unique=True, nullable=False)   # ex: "2024-2025"
    actif = db.Column(db.Boolean, default=True)
    processus_lance = db.Column(db.Boolean, default=False, nullable=False)
    liste_finalisee = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f'<AnneeDiplomation {self.code}>'
