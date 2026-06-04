from app import db


class ListeFinissants(db.Model):
    """
    Liste officielle des étudiants ayant validé leur année académique
    et autorisés à poursuivre la diplomation.
    Importée par l'admin depuis les résultats du jury.
    """
    __tablename__ = 'liste_finissants'

    id = db.Column(db.Integer, primary_key=True)
    matricule = db.Column(db.String(20), nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    filiere = db.Column(db.String(20))
    annee_academique = db.Column(db.String(9), nullable=False)
    valide = db.Column(db.Boolean, default=True, nullable=False)
    motif_invalidation = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    __table_args__ = (
        db.UniqueConstraint('matricule', 'annee_academique', name='uq_finissant_annee'),
    )

    def __repr__(self):
        return f'<Finissant {self.matricule} — {self.nom} {self.prenom}>'
