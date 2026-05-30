from app import db


class DossierFormalisation(db.Model):
    __tablename__ = 'dossier_formalisation'

    id_formalisation = db.Column(db.Integer, primary_key=True)
    id_dossier = db.Column(
        db.Integer, db.ForeignKey('dossier_diplomation.id_dossier'), unique=True, nullable=False
    )
    matricule = db.Column(db.String(20), db.ForeignKey('etudiant.matricule'), nullable=False)
    date_constitution = db.Column(db.DateTime, server_default=db.func.now())
    statut = db.Column(db.String(20), default='EN_ATTENTE')

    recu_quitus_cycle = db.Column(db.Boolean, default=False)
    quitus_non_redevance = db.Column(db.Boolean, default=False)
    attestation_depot_memoire = db.Column(db.Boolean, default=False)
    recu_association_etudiants = db.Column(db.Boolean, default=False)
    photocopie_cni = db.Column(db.Boolean, default=False)
    photocopie_badge_etudiant = db.Column(db.Boolean, default=False)
    quitus_bibliotheque = db.Column(db.Boolean, default=False)
    date_signature_registre = db.Column(db.DateTime)
    annee_academique = db.Column(db.String(9))

    def __repr__(self):
        return f'<Formalisation {self.id_formalisation} — {self.matricule}>'
