from app import db


class Filiere(db.Model):
    __tablename__ = 'filiere'

    id_filiere = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    nom  = db.Column(db.String(150), nullable=False)
    cycle = db.Column(db.String(30))
    actif = db.Column(db.Boolean, default=True)

    code_departement = db.Column(db.String(20), db.ForeignKey('departement.code'), nullable=True)

    def __repr__(self):
        return f'<Filiere {self.code} — {self.nom}>'
