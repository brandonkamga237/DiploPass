from app import db


STATUTS_DIPLOMATION = [
    'DEPOSE', 'EN_VERIFICATION', 'INCOMPLET',
    'AUTHENTIFICATION', 'AUTH_REJETEE',
    'LISTE_FINISSANTS', 'IMPRESSION_PROVISOIRE',
    'PRODUCTION_DEFINITIVE', 'SIGNATURE_DIRECTEUR',
    'SIGNATURE_RECTEUR', 'SIGNATURE_MINISTRE',
    'FORMALISATION', 'CLOTURE', 'REJETE',
]


class DossierDiplomation(db.Model):
    __tablename__ = 'dossier_diplomation'

    id_dossier = db.Column(db.Integer, primary_key=True)
    matricule = db.Column(db.String(20), db.ForeignKey('etudiant.matricule'), nullable=False)
    date_depot = db.Column(db.DateTime, server_default=db.func.now())
    statut = db.Column(db.String(30), nullable=False, default='DEPOSE')

    montant_frais = db.Column(db.Numeric(10, 2))
    frais_payes = db.Column(db.Boolean, default=False)

    resultat_authentification = db.Column(db.String(15))
    nom_sur_diplome = db.Column(db.String(150))
    prenom_sur_diplome = db.Column(db.String(150))
    ddn_sur_diplome = db.Column(db.Date)
    lddn_sur_diplome = db.Column(db.String(150))

    statut_production_diplome = db.Column(db.String(30))
    date_signature_directeur = db.Column(db.Date)
    date_signature_recteur = db.Column(db.Date)
    date_signature_ministre = db.Column(db.Date)
    type_diplome = db.Column(db.String(50))
    est_diplome_conforme = db.Column(db.Boolean)

    annee_academique = db.Column(db.String(9))
    observations = db.Column(db.Text)
    date_limite_depot = db.Column(db.Date)

    signature_empreinte_registre = db.Column(db.Boolean, default=False)
    toge_remise = db.Column(db.Boolean, default=False)
    journal_promo_remis = db.Column(db.Boolean, default=False)
    motif_rejet = db.Column(db.Text)

    # Communiqué qui a déclenché l'ouverture du processus
    id_communique = db.Column(db.Integer, db.ForeignKey('communique.id_communique'), nullable=True)


    id_representant = db.Column(
        db.Integer, db.ForeignKey('representant_filiere.id_representant'), nullable=True
    )
    id_chef_bureau = db.Column(
        db.Integer, db.ForeignKey('chef_bureau_diplomation.id_chef_bureau'), nullable=True
    )

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime, server_default=db.func.now(), onupdate=db.func.now()
    )

    historique     = db.relationship('HistoriquePhases', backref='dossier', lazy=True)
    pieces_jointes = db.relationship('PieceJointe', backref='dossier', lazy=True,
                                     cascade='all, delete-orphan')
    formalisation  = db.relationship(
        'DossierFormalisation', backref='dossier_diplomation', uselist=False, lazy=True
    )

    chef_bureau = db.relationship(
        'ChefBureauDiplomation',
        foreign_keys=[id_chef_bureau],
        backref='dossiers',
        lazy=True,
    )

    def libelle_statut(self):
        labels = {
            'DEPOSE': 'Déposé',
            'EN_VERIFICATION': 'En vérification',
            'INCOMPLET': 'Incomplet',
            'AUTHENTIFICATION': 'Authentification',
            'AUTH_REJETEE': 'Auth. rejetée',
            'LISTE_FINISSANTS': 'Liste finissants',
            'IMPRESSION_PROVISOIRE': 'Impression provisoire',
            'PRODUCTION_DEFINITIVE': 'Production définitive',
            'SIGNATURE_DIRECTEUR': 'Signature Directeur',
            'SIGNATURE_RECTEUR': 'Signature Recteur',
            'SIGNATURE_MINISTRE': 'Signature Ministre',
            'FORMALISATION': 'Formalisation',
            'CLOTURE': 'Clôturé',
            'REJETE': 'Rejeté',
        }
        return labels.get(self.statut, self.statut)

    def couleur_statut(self):
        couleurs = {
            'DEPOSE':               'success',
            'EN_VERIFICATION':      'success',
            'INCOMPLET':            'warning',
            'AUTHENTIFICATION':     'success',
            'AUTH_REJETEE':         'danger',
            'LISTE_FINISSANTS':     'success',
            'IMPRESSION_PROVISOIRE':'success',
            'PRODUCTION_DEFINITIVE':'success',
            'SIGNATURE_DIRECTEUR':  'success',
            'SIGNATURE_RECTEUR':    'success',
            'SIGNATURE_MINISTRE':   'success',
            'FORMALISATION':        'success',
            'CLOTURE':              'success',
            'REJETE':               'danger',
        }
        return couleurs.get(self.statut, 'success')

    def __repr__(self):
        return f'<Dossier {self.id_dossier} — {self.matricule} — {self.statut}>'
