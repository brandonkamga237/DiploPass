import os
import pytest
import datetime
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import create_app, db
from app.models.etudiant import Etudiant
from app.models.representant import RepresentantFiliere
from app.models.dossier_diplomation import DossierDiplomation
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    app = create_app('development')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        db.create_all()
        _seed()
        yield app
        db.drop_all()


def _seed():
    e = Etudiant(
        matricule='ETU001',
        nom='KAMGA',
        prenom='Paul',
        date_naissance=datetime.date(2001, 5, 10),
        filiere='Génie Informatique',
        mot_de_passe=generate_password_hash('ETU001'),
    )
    r = RepresentantFiliere(
        nom='NKENG',
        prenom='Marc',
        filiere_geree='Génie Informatique',
        login='rep.gi',
        mot_de_passe=generate_password_hash('rep123'),
    )
    db.session.add_all([e, r])
    db.session.commit()

    d = DossierDiplomation(
        matricule='ETU001',
        statut='DEPOSE',
        annee_academique='2024-2025',
        id_representant=r.id_representant,
    )
    db.session.add(d)
    db.session.commit()


@pytest.fixture
def client(app):
    return app.test_client()


def test_dossier_cree(app):
    with app.app_context():
        d = DossierDiplomation.query.filter_by(matricule='ETU001').first()
        assert d is not None
        assert d.statut == 'DEPOSE'


def test_libelle_statut(app):
    with app.app_context():
        d = DossierDiplomation.query.filter_by(matricule='ETU001').first()
        assert d.libelle_statut() == 'Déposé'


def test_couleur_statut(app):
    with app.app_context():
        d = DossierDiplomation.query.filter_by(matricule='ETU001').first()
        assert d.couleur_statut() == 'secondary'


def test_transition_statut(app):
    with app.app_context():
        d = DossierDiplomation.query.filter_by(matricule='ETU001').first()
        d.statut = 'EN_VERIFICATION'
        db.session.commit()
        d2 = DossierDiplomation.query.get(d.id_dossier)
        assert d2.statut == 'EN_VERIFICATION'
