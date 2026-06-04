from app import db


STATUTS_CORRECTION = ['BROUILLON', 'CORRIGE', 'TRANSMIS']


class ListeFinissants(db.Model):
    """
    Liste officielle des finissants importée par l'admin.
    Les représentants corrigent les données par filière,
    puis transmettent au Chef de Bureau pour impression.
    Ce sont ces données (corrigées) qui figureront sur les diplômes.
    """
    __tablename__ = 'liste_finissants'

    id               = db.Column(db.Integer, primary_key=True)
    matricule        = db.Column(db.String(20), nullable=False)
    nom              = db.Column(db.String(100), nullable=False)
    prenom           = db.Column(db.String(100), nullable=False)
    date_naissance   = db.Column(db.Date)
    lieu_naissance   = db.Column(db.String(150))
    filiere          = db.Column(db.String(20))
    cycle            = db.Column(db.String(20))
    annee_academique = db.Column(db.String(9), nullable=False)

    # Validation
    valide             = db.Column(db.Boolean, default=True, nullable=False)
    motif_invalidation = db.Column(db.Text)

    # Statut de correction par le représentant
    # BROUILLON → représentant n'a pas encore validé ses corrections
    # CORRIGE   → représentant a corrigé, prêt à transmettre
    # TRANSMIS  → transmis au Chef de Bureau, données copiées dans le dossier
    statut_correction = db.Column(db.String(20), default='BROUILLON', nullable=False)

    created_at  = db.Column(db.DateTime, server_default=db.func.now())
    updated_at  = db.Column(db.DateTime, server_default=db.func.now(),
                            onupdate=db.func.now())

    __table_args__ = (
        db.UniqueConstraint('matricule', 'annee_academique', name='uq_finissant_annee'),
    )

    def __repr__(self):
        return f'<Finissant {self.matricule} — {self.nom} {self.prenom} [{self.statut_correction}]>'
