import os

from flask import request
from flask_babel import Babel
from flask_login import LoginManager
from flask_login import current_user

from . import auth
from . import mail
from . import models
from . import utils
from . import validate
from .database import db
from .models import Counter
from .models import User

__all__ = [
    "GFlaskAuth",
    "db",
    "utils",
    "validate",
    "mail",
    "Counter",
    "User",
]

# Istanziamo Babel (verrà attaccato all'app in init_app)
babel = Babel()


def get_locale():
    if current_user.is_authenticated and getattr(current_user, "locale", None):
        return current_user.locale
    return request.accept_languages.best_match(auth.LANGUAGES)


class GFlaskAuth:
    """
    Estensione Flask per l'autenticazione.
    Inizializza il database, Flask-Login, Babel e le rotte.
    """

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        # 1. Configurazioni di default se l'app Host non le ha
        app.config.setdefault("APP_NAME", "Flask App")
        app.config.setdefault("BABEL_DEFAULT_LOCALE", "it")

        if "EMAIL" not in app.config:
            app.config["EMAIL"] = self._load_email_config()

        # 2. Inizializzazione Database
        if "DATABASE_URL" in app.config:
            db.init_app(app.config["DATABASE_URL"])
            with app.app_context():
                models.create_all()

        # 3. Inizializzazione Babel
        babel.init_app(app, locale_selector=get_locale)

        # 4. Inizializzazione Flask-Login
        login_manager = LoginManager()
        login_manager.login_view = "auth.login"
        login_manager.init_app(app)

        @login_manager.user_loader
        def load_user(user_id):
            return models.User.get(user_id)

        # 5. Registrazione del Blueprint
        app.register_blueprint(auth.bp)

    def _load_email_config(self):
        email_config = {}
        for key, value in os.environ.items():
            if key.startswith("EMAIL_"):
                config_key = key[6:].lower()
                if config_key == "smtp_port":
                    value = int(value)
                email_config[config_key] = value
        return email_config
