from app import db


class HistoriquePhases(db.Model):
    __tablename__ = 'historique_phases'

    id_historique = db.Column(db.Integer, primary_key=True)
    id_dossier = db.Column(
        db.Integer, db.ForeignKey('dossier_diplomation.id_dossier'), nullable=False
    )
    phase = db.Column(db.String(50), nullable=False)
    ancien_statut = db.Column(db.String(30))
    nouveau_statut = db.Column(db.String(30))
    commentaire = db.Column(db.Text)
    id_acteur = db.Column(db.Integer)
    role_acteur = db.Column(db.String(50))
    date_action = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f'<Historique {self.id_historique} — {self.phase}>'
