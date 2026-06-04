from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models.etudiant import Etudiant
from app.models.directeur import Directeur
from app.models.chef_service import ChefServiceScolarite
from app.models.representant import RepresentantFiliere
from app.models.admin import Admin

auth_bp = Blueprint('auth', __name__)

ROLE_REDIRECTS = {
    'directeur':    'directeur.dashboard',
    'chef_service': 'chef_service.dashboard',
    'chef_bureau':  'chef_bureau.dashboard',
    'representant': 'representant.dashboard',
    'etudiant':     'etudiant.dashboard',
    'admin':        'admin.dashboard',
}


@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        role = session.get('role', '')
        return redirect(url_for(ROLE_REDIRECTS.get(role, 'auth.login')))
    return render_template('home.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        role = session.get('role', '')
        return redirect(url_for(ROLE_REDIRECTS.get(role, 'auth.login')))

    if request.method == 'POST':
        identifiant = request.form.get('identifiant', '').strip()
        mdp = request.form.get('mot_de_passe', '')

        user, role = _auto_detecter(identifiant, mdp)
        if user:
            login_user(user)
            session['role'] = role
            return redirect(url_for(ROLE_REDIRECTS[role]))

        flash('Identifiant ou mot de passe incorrect.', 'danger')

    return render_template('auth/login.html')


def _auto_detecter(identifiant, mdp):
    """
    Détecte automatiquement le type d'utilisateur à partir de l'identifiant et
    du mot de passe, sans que l'utilisateur ait à préciser son rôle.
    Ordre de tentative : Etudiant → Représentant/Chef Bureau → Directeur
                         → Chef Service → Admin
    """
    # 1. Étudiant — identifiant = matricule (clé primaire)
    etu = Etudiant.query.get(identifiant)
    if etu and etu.actif and etu.check_password(mdp):
        return etu, 'etudiant'

    # 2. Représentant / Chef de Bureau (même table, même login)
    rep = RepresentantFiliere.query.filter_by(login=identifiant, actif=True).first()
    if rep and rep.check_password(mdp):
        return rep, rep.role_effectif   # 'representant' ou 'chef_bureau'

    # 3. Directeur
    dir_ = Directeur.query.filter_by(login=identifiant, actif=True).first()
    if dir_ and dir_.check_password(mdp):
        return dir_, 'directeur'

    # 4. Chef Service Scolarité
    cs = ChefServiceScolarite.query.filter_by(login=identifiant, actif=True).first()
    if cs and cs.check_password(mdp):
        return cs, 'chef_service'

    # 5. Admin
    adm = Admin.query.filter_by(login=identifiant, actif=True).first()
    if adm and adm.check_password(mdp):
        return adm, 'admin'

    return None, None


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/annee/<code>')
@login_required
def changer_annee(code):
    from app.models.annee_diplomation import AnneeDiplomation
    annee = AnneeDiplomation.query.filter_by(code=code).first()
    if annee:
        session['annee_active_code'] = code
    next_url = request.referrer or url_for('auth.index')
    return redirect(next_url)
