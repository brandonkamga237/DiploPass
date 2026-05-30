from app import db


class Communique(db.Model):
    __tablename__ = 'communique'

    id_communique = db.Column(db.Integer, primary_key=True)
    numero_communique = db.Column(db.String(50), unique=True, nullable=False)
    titre = db.Column(db.String(255), nullable=False)
    contenu = db.Column(db.Text)
    date_emission = db.Column(db.Date, nullable=False)
    date_limite_depot = db.Column(db.Date)
    annee_academique = db.Column(db.String(9), nullable=False)
    objet = db.Column(db.String(255))
    type_processus = db.Column(db.String(20))
    statut = db.Column(db.String(20), default='BROUILLON')
    id_directeur = db.Column(db.Integer, db.ForeignKey('directeur.id_directeur'))
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def is_ouvert(self):
        import datetime
        today = datetime.date.today()
        return (
            self.statut == 'PUBLIE'
            and (self.date_limite_depot is None or self.date_limite_depot >= today)
        )

    def __repr__(self):
        return f'<Communique {self.numero_communique}>'
