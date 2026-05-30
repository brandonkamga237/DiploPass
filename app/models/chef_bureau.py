from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class ChefBureauDiplomation(UserMixin, db.Model):
    __tablename__ = 'chef_bureau_diplomation'

    id_chef_bureau = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    login = db.Column(db.String(100), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    actif = db.Column(db.Boolean, default=True)

    def get_id(self):
        return f'chef_bureau:{self.id_chef_bureau}'

    def set_password(self, raw):
        self.mot_de_passe = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.mot_de_passe, raw)

    @property
    def nom_complet(self):
        return f'{self.nom} {self.prenom}'

    def __repr__(self):
        return f'<ChefBureau {self.login}>'
