from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
import click
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app():
    load_dotenv()
    app = Flask(__name__)

    app.config.from_object('app.config.Config')

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'crm_auth.login'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import AdminUser
        return db.session.get(AdminUser, int(user_id))

    # Register blueprints
    from app.routes.public import public
    from app.routes.api import api
    from app.routes.crm.auth import crm_auth
    from app.routes.crm.dashboard import crm_dashboard
    from app.routes.crm.projects import crm_projects
    from app.routes.crm.testimonials import crm_testimonials
    from app.routes.crm.contacts import crm_contacts
    from app.routes.crm.notebooks import crm_notebooks
    from app.routes.crm.skills import crm_skills
    from app.routes.crm.settings import crm_settings
    from app.routes.crm.hire_requests import crm_hire_requests
    from app.routes.crm.pm import crm_pm
    from app.routes.crm.active_projects import crm_active_projects
    from app.routes.crm.reviews import crm_reviews
    from app.routes.blog import blog
    from app.routes.crm.blog import crm_blog

    app.register_blueprint(public)
    app.register_blueprint(blog)
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(crm_auth, url_prefix='/admin')
    app.register_blueprint(crm_dashboard, url_prefix='/admin')
    app.register_blueprint(crm_projects, url_prefix='/admin/projects')
    app.register_blueprint(crm_testimonials, url_prefix='/admin/testimonials')
    app.register_blueprint(crm_contacts, url_prefix='/admin/contacts')
    app.register_blueprint(crm_notebooks, url_prefix='/admin/notebooks')
    app.register_blueprint(crm_skills, url_prefix='/admin/skills')
    app.register_blueprint(crm_settings, url_prefix='/admin/settings')
    app.register_blueprint(crm_hire_requests, url_prefix='/admin/hire-requests')
    app.register_blueprint(crm_pm, url_prefix='/admin/pm')
    app.register_blueprint(crm_active_projects, url_prefix='/admin/active-projects')
    app.register_blueprint(crm_reviews, url_prefix='/admin/reviews')
    app.register_blueprint(crm_blog, url_prefix='/admin/blog')

    # Jinja2 helpers
    from app.utils.helpers import format_date, slugify, get_setting
    app.jinja_env.globals['format_date'] = format_date
    app.jinja_env.globals['get_setting'] = get_setting

    # Context processor for settings
    @app.context_processor
    def inject_settings():
        from app.models import Setting, ActiveProject
        settings = {}
        try:
            for s in db.session.query(Setting).all():
                settings[s.key] = s.value
        except Exception:
            pass

        # Get current active project for "James is working on..."
        current_project = None
        try:
            current_project = db.session.query(ActiveProject).filter_by(
                status='in_progress', is_private=False, is_anonymous=False
            ).first()
        except Exception:
            pass

        return dict(settings=settings, current_active_project=current_project)

    # CLI commands
    @app.cli.command('create-admin')
    @click.option('--email', prompt=True)
    @click.option('--password', prompt=True, hide_input=True)
    def create_admin(email, password):
        """Create the admin account."""
        import bcrypt
        from app.models import AdminUser
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        admin = AdminUser(email=email, password_hash=hashed)
        db.session.add(admin)
        db.session.commit()
        click.echo(f"Admin created: {email}")

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return app.send_static_file('404.html') if os.path.exists(
            os.path.join(app.static_folder, '404.html')
        ) else ('<h1>404 - Page Not Found</h1>', 404)

    @app.errorhandler(500)
    def server_error(e):
        return '<h1>500 - Server Error</h1>', 500

    return app
