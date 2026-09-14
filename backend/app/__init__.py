from flask import Flask
from flask_migrate import Migrate
from app.core.config import Config
from app.core.db import db

# Wczytujemy wszystkie modele, aby Flask-Migrate / Alembic je wykrył
from app.portal.models import UserProfile
from app.cookbook.models import Recipe

migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    from app.portal.routes import portal_bp
    from app.cookbook.routes import cookbook_bp

    app.register_blueprint(portal_bp, url_prefix="/api/portal")
    app.register_blueprint(cookbook_bp, url_prefix="/api/cookbook")

    return app
