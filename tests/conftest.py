import os

import pytest
from flask import Flask
from werkzeug.security import generate_password_hash

from gflask import GFlaskAuth
from gflask import main
from gflask.database import db
from gflask.models import User


@pytest.fixture
def app():
    """Crea e configura un'app Host fittizia a cui attaccare la libreria."""
    os.environ["FLASK_TESTING"] = "true"

    # 1. Creiamo un'app Flask nuda e cruda (come farebbe l'utente finale)
    app = Flask(__name__)
    app.config.update(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "DATABASE_URL": "sqlite:///:memory:",
            "SECRET_KEY": "super-secret-key-for-tests",
        }
    )

    # 2. Inizializziamo l'estensione GFlaskAuth passandole l'app
    auth_extension = GFlaskAuth()
    auth_extension.init_app(app)

    # 3. Registriamo il blueprint 'main' per simulare le rotte dell'app ospite
    app.register_blueprint(main.bp)

    yield app

    # Pulizia
    with app.app_context():
        from gflask import models

        models.drop_all()


@pytest.fixture
def client(app):
    """Un client di test per fare richieste HTTP."""
    return app.test_client()


# Non serve perche' mail.send testa current_app.testing e se vero
# non invia la mail ed esegue solo il logging
# @pytest.fixture(autouse=True)
# def disable_emails(monkeypatch):
#     """Blocca l'invio reale delle email in tutti i test."""
#     monkeypatch.setattr(
#         "gflask.mail.send", lambda args, pard=None: {"status": "Success"}
#     )


@pytest.fixture
def verified_user(app):
    """Crea un utente già verificato nel DB per i test."""
    with app.app_context():
        user = User(
            email="test@example.com",
            name="Test User",
            password=generate_password_hash("Password123!"),
            locale="it",
        )
        user.add()
        # Chiamiamo la funzione per forzare l'aggiornamento su DB a 1
        user.verified()
        return User.get(user.user_id)
