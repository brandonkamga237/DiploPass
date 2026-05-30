from app import db

# Table pivot M-N : un communiqué peut cibler plusieurs promotions
communique_promotion = db.Table(
    'communique_promotion',
    db.Column('id_communique', db.Integer,
              db.ForeignKey('communique.id_communique', ondelete='CASCADE'),
              primary_key=True),
    db.Column('id_promotion', db.Integer,
              db.ForeignKey('promotion.id_promotion', ondelete='CASCADE'),
              primary_key=True),
)


class Promotion(db.Model):
    """
    Promotion = filière + niveau + année académique.
    Représente la cohorte d'étudiants finissants d'une même filière pour une année donnée.
    Niveau 3 → Licence ; Niveau 5 → Master.
    """
    __tablename__ = 'promotion'

    id_promotion = db.Column(db.Integer, primary_key=True)
    code_filiere = db.Column(db.String(20), db.ForeignKey('filiere.code'), nullable=False)
    annee_academique = db.Column(db.String(9), nullable=False)   # ex: "2023-2024"
    niveau = db.Column(db.Integer, nullable=False)               # 3 ou 5
    actif = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    filiere = db.relationship('Filiere', backref='promotions')
    etudiants = db.relationship('Etudiant', backref='promotion_obj', lazy=True)

    @property
    def libelle_niveau(self):
        return {3: 'Licence', 5: 'Master'}.get(self.niveau, f'Niv.{self.niveau}')

    @property
    def libelle(self):
        return f'{self.libelle_niveau} {self.code_filiere} — {self.annee_academique}'

    def __repr__(self):
        return f'<Promotion {self.libelle}>'
