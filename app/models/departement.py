from app import db


class Departement(db.Model):
    __tablename__ = 'departement'

    code = db.Column(db.String(20), primary_key=True)
    nom  = db.Column(db.String(150), nullable=False)
    actif = db.Column(db.Boolean, default=True)

    filieres = db.relationship('Filiere', backref='departement_obj', lazy=True,
                               foreign_keys='Filiere.code_departement')

    representants = db.relationship('RepresentantFiliere', backref='departement_obj',
                                    lazy=True, foreign_keys='RepresentantFiliere.code_departement')

    def __repr__(self):
        return f'<Departement {self.code} — {self.nom}>'
