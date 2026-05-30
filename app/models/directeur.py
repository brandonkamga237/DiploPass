from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class Directeur(UserMixin, db.Model):
    __tablename__ = 'directeur'

    id_directeur = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.String(100))
    login = db.Column(db.String(100), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    actif = db.Column(db.Boolean, default=True)

    communiques = db.relationship('Communique', backref='directeur', lazy=True)

    def get_id(self):
        return f'directeur:{self.id_directeur}'

    def set_password(self, raw):
        self.mot_de_passe = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.mot_de_passe, raw)

    @property
    def nom_complet(self):
        return f'{self.nom} {self.prenom}'

    def __repr__(self):
        return f'<Directeur {self.login}>'
