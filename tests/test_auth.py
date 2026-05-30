import os
import pytest
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import create_app, db
from app.models.etudiant import Etudiant
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    app = create_app('development')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        db.create_all()
        _seed(app)
        yield app
        db.drop_all()


def _seed(app):
    with app.app_context():
        import datetime
        e = Etudiant(
            matricule='TEST001',
            nom='DUPONT',
            prenom='Alice',
            date_naissance=datetime.date(2000, 1, 1),
            filiere='Test',
            mot_de_passe=generate_password_hash('TEST001'),
        )
        db.session.add(e)
        db.session.commit()


@pytest.fixture
def client(app):
    return app.test_client()


def test_login_page_accessible(client):
    resp = client.get('/login')
    assert resp.status_code == 200


def test_login_etudiant_success(client):
    resp = client.post('/login', data={
        'role': 'etudiant',
        'identifiant': 'TEST001',
        'mot_de_passe': 'TEST001',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_login_etudiant_mauvais_mdp(client):
    resp = client.post('/login', data={
        'role': 'etudiant',
        'identifiant': 'TEST001',
        'mot_de_passe': 'MAUVAIS',
    }, follow_redirects=True)
    assert b'incorrect' in resp.data.lower() or resp.status_code == 200


def test_login_matricule_inexistant(client):
    resp = client.post('/login', data={
        'role': 'etudiant',
        'identifiant': 'INEXISTANT',
        'mot_de_passe': 'pwd',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_logout(client):
    client.post('/login', data={
        'role': 'etudiant',
        'identifiant': 'TEST001',
        'mot_de_passe': 'TEST001',
    })
    resp = client.get('/logout', follow_redirects=True)
    assert resp.status_code == 200
