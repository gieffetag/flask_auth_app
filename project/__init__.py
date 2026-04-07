from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager

from . import auth
from . import main
from . import models
from .database import db

load_dotenv()


def create_app():
    # Istanzio la app
    app = Flask(__name__)

    # Carico le variabili di ambiente
    app.config.from_prefixed_env()
    app.config["APP_NAME"] = "FlaskAuthApp"

    # Inizializzazione e gestione del database
    db.init_app(app.config["DATABASE_URL"])
    models.create_all()

    # python -m flask --app mymusic shell
    @app.shell_context_processor
    def make_shell_context():
        return {"db": db, "models": models, "app": app}

    # Configure Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    # User loader function for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return models.User.get(user_id)

    # Register blueprints
    # app.register_blueprint(pages.bp, url_prefix="/")
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)

    return app
