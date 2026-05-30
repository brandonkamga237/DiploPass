from app import db, login_mgr
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class Etudiant(UserMixin, db.Model):
    __tablename__ = 'etudiant'

    matricule = db.Column(db.String(20), primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    date_naissance = db.Column(db.Date, nullable=False)
    lieu_naissance = db.Column(db.String(150))
    filiere = db.Column(db.String(100), nullable=False)
    niveau = db.Column(db.Integer)
    cycle = db.Column(db.String(20))
    type_etudiant = db.Column(db.String(20), default='REGULIER')
    statut_fonctionnaire = db.Column(db.Boolean, default=False)
    email = db.Column(db.String(150), unique=True)
    telephone = db.Column(db.String(20))
    numero_cni = db.Column(db.String(50))
    promotion = db.Column(db.String(20))
    sexe = db.Column(db.String(1))
    mot_de_passe = db.Column(db.String(255), nullable=False)
    annee_academique = db.Column(db.String(9))
    actif = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


    dossier_diplomation = db.relationship(
        'DossierDiplomation', backref='etudiant', uselist=False, lazy=True
    )
    dossier_integration = db.relationship(
        'DossierIntegration', backref='etudiant', uselist=False, lazy=True
    )

    def get_id(self):
        return f'etudiant:{self.matricule}'

    def set_password(self, raw):
        self.mot_de_passe = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.mot_de_passe, raw)

    @property
    def nom_complet(self):
        return f'{self.nom} {self.prenom}'

    def __repr__(self):
        return f'<Etudiant {self.matricule} — {self.nom} {self.prenom}>'


@login_mgr.user_loader
def load_user(user_id):
    from app.models.directeur import Directeur
    from app.models.chef_service import ChefServiceScolarite
    from app.models.representant import RepresentantFiliere

    prefix, _, pk = user_id.partition(':')
    if prefix == 'etudiant':
        return Etudiant.query.get(pk)
    if prefix == 'directeur':
        return Directeur.query.get(int(pk))
    if prefix == 'chef_service':
        return ChefServiceScolarite.query.get(int(pk))
    if prefix == 'representant':
        return RepresentantFiliere.query.get(int(pk))
    if prefix == 'admin':
        from app.models.admin import Admin
        return Admin.query.get(int(pk))
    return None
