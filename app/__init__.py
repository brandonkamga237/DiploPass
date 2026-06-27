from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import config
import os

db = SQLAlchemy()
migrate = Migrate()
login_mgr = LoginManager()
login_mgr.login_view = 'auth.login'
login_mgr.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_mgr.login_message_category = 'warning'


def create_app(env=None):
    app = Flask(__name__)
    env = env or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[env])

    db.init_app(app)
    migrate.init_app(app, db)
    login_mgr.init_app(app)

    # Import de tous les modèles pour Flask-Migrate
    from app.models import piece_jointe  # noqa: F401

    from app.controllers.auth import auth_bp
    from app.controllers.admin import admin_bp
    from app.controllers.directeur import directeur_bp
    from app.controllers.chef_service import chef_service_bp
    from app.controllers.chef_bureau import chef_bureau_bp
    from app.controllers.representant import representant_bp
    from app.controllers.etudiant import etudiant_bp
    from app.controllers.notifications import notif_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(directeur_bp, url_prefix='/directeur')
    app.register_blueprint(chef_service_bp, url_prefix='/chef-service')
    app.register_blueprint(chef_bureau_bp, url_prefix='/chef-bureau')
    app.register_blueprint(representant_bp, url_prefix='/representant')
    app.register_blueprint(etudiant_bp, url_prefix='/etudiant')
    app.register_blueprint(notif_bp, url_prefix='/notifications')

    # ── Context processor : notifications non lues ───────────────────────────
    @app.context_processor
    def inject_notifs():
        from flask import session
        from flask_login import current_user
        if not current_user or not current_user.is_authenticated:
            return dict(nb_notifs_non_lues=0, notifs_recentes=[])
        try:
            from app.models.notification import Notification
            role = session.get('role', '')
            if role == 'etudiant':
                return dict(nb_notifs_non_lues=0, notifs_recentes=[])
            q = Notification.query.filter_by(destinataire_type=role, lue=False)
            nb = q.count()
            recentes = (
                Notification.query
                .filter_by(destinataire_type=role)
                .order_by(Notification.created_at.desc())
                .limit(5).all()
            )
            return dict(nb_notifs_non_lues=nb, notifs_recentes=recentes)
        except Exception:
            return dict(nb_notifs_non_lues=0, notifs_recentes=[])

    # ── Context processor : année académique active ───────────────────────────
    @app.context_processor
    def inject_annee_active():
        from flask import session
        from flask_login import current_user
        if not current_user or not current_user.is_authenticated:
            return {}
        try:
            from app.models.annee_diplomation import AnneeDiplomation
            role = session.get('role', '')

            if role == 'admin':
                # L'admin peut naviguer entre toutes les années (archives incluses)
                toutes = AnneeDiplomation.query.order_by(
                    AnneeDiplomation.code.desc()
                ).all()
                code = session.get('annee_active_code')
                if not code and toutes:
                    code = toutes[0].code
                    session['annee_active_code'] = code
                annee_active = next(
                    (a for a in toutes if a.code == code),
                    toutes[0] if toutes else None,
                )
                annee_la_plus_recente = toutes[0] if toutes else None
                est_archive = bool(
                    annee_active and annee_la_plus_recente
                    and annee_active.code != annee_la_plus_recente.code
                )
                return dict(
                    annee_active=annee_active,
                    toutes_annees=toutes,
                    est_archive=est_archive,
                )
            else:
                # Tous les autres rôles : toujours l'année la plus récente
                annee_courante = (
                    AnneeDiplomation.query
                    .order_by(AnneeDiplomation.code.desc())
                    .first()
                )
                if annee_courante:
                    session['annee_active_code'] = annee_courante.code
                return dict(
                    annee_active=annee_courante,
                    toutes_annees=[],
                    est_archive=False,
                )
        except Exception:
            return {}

    return app
