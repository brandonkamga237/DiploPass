from app import db


class Filiere(db.Model):
    __tablename__ = 'filiere'

    id_filiere = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)   # ex: GI, GC, EEA
    nom = db.Column(db.String(150), nullable=False)                 # ex: Génie Informatique
    cycle = db.Column(db.String(30))                                # Licence, Master, Ingénieur
    actif = db.Column(db.Boolean, default=True)

    representants = db.relationship('RepresentantFiliere', backref='filiere_obj', lazy=True, foreign_keys='RepresentantFiliere.code_filiere')

    def __repr__(self):
        return f'<Filiere {self.code} — {self.nom}>'
