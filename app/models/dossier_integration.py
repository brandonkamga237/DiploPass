from app import db


class DossierIntegration(db.Model):
    __tablename__ = 'dossier_integration'

    id_dossier_integration = db.Column(db.Integer, primary_key=True)
    matricule = db.Column(db.String(20), db.ForeignKey('etudiant.matricule'), nullable=False)
    date_depot = db.Column(db.DateTime, server_default=db.func.now())
    statut = db.Column(db.String(30), default='EN_CONSTITUTION')

    frais_visite_medicale = db.Column(db.Boolean, default=False)
    photocopie_cni = db.Column(db.Boolean, default=False)
    photocopie_acte_naissance = db.Column(db.Boolean, default=False)
    photocopie_dipet = db.Column(db.Boolean, default=False)
    demi_cartes_photos = db.Column(db.Boolean, default=False)
    dactylographie_attestation = db.Column(db.Boolean, default=False)
    bordereau = db.Column(db.Boolean, default=False)
    signature_correspondance_dir = db.Column(db.Boolean, default=False)

    observations = db.Column(db.Text)
    annee_academique = db.Column(db.String(9))
    lieu_affectation = db.Column(db.String(200))
    date_prise_service = db.Column(db.Date)
    heure_prise_service = db.Column(db.Time)
    date_transmission_minfopra = db.Column(db.Date)
    date_limite_depot = db.Column(db.Date)

    id_representant = db.Column(
        db.Integer, db.ForeignKey('representant_filiere.id_representant')
    )
    id_chef_bureau = db.Column(
        db.Integer, db.ForeignKey('chef_bureau_diplomation.id_chef_bureau')
    )

    def __repr__(self):
        return f'<Integration {self.id_dossier_integration} — {self.matricule}>'
