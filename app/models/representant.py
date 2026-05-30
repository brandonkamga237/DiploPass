from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class RepresentantFiliere(UserMixin, db.Model):
    """
    Représentant de filière — membre de la scolarité rattaché à une filière.
    Peut être promu Chef de Bureau de la Diplomation (est_chef_bureau=True)
    par le Chef Service, le Directeur ou l'Admin.

    Capacités de base (tout représentant) :
      - Réceptionner et vérifier les dossiers des étudiants de sa filière
      - Corriger les informations sur la liste des finissants
      - Gérer la formalisation (phase 7)

    Capacités supplémentaires si est_chef_bureau=True :
      - Envoyer les demandes d'authentification aux universités
      - Lancer les impressions provisoires et définitives
      - Vérifier les cachets (Directeur, Recteur, Ministre)
    """
    __tablename__ = 'representant_filiere'

    id_representant = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    login = db.Column(db.String(100), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    actif = db.Column(db.Boolean, default=True)

    # Filière représentée — texte libre (rétrocompat) + FK optionnelle vers filiere.code
    filiere_geree = db.Column(db.String(100), nullable=False)
    code_filiere = db.Column(db.String(20), db.ForeignKey('filiere.code'), nullable=True)
    bureau = db.Column(db.String(100))

    # Promotion : True = ce représentant est aussi Chef de Bureau de la Diplomation
    est_chef_bureau = db.Column(db.Boolean, default=False, nullable=False)

    dossiers = db.relationship('DossierDiplomation', backref='representant', lazy=True)

    def get_id(self):
        return f'representant:{self.id_representant}'

    def set_password(self, raw):
        self.mot_de_passe = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.mot_de_passe, raw)

    @property
    def nom_complet(self):
        return f'{self.prenom} {self.nom}'

    @property
    def role_effectif(self):
        """Rôle à stocker en session après login."""
        return 'chef_bureau' if self.est_chef_bureau else 'representant'

    def __repr__(self):
        role = 'Chef Bureau' if self.est_chef_bureau else 'Représentant'
        return f'<{role} {self.login} — {self.filiere_geree}>'
