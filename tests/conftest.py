import os

import pytest
from werkzeug.security import generate_password_hash

from gflask import create_app
from gflask.database import db
from gflask.models import User


@pytest.fixture
def app():
    """Crea e configura una nuova istanza dell'app per ogni test."""
    os.environ["FLASK_TESTING"] = "true"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["SECRET_KEY"] = "super-secret-key-for-tests"

    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "BABEL_DEFAULT_LOCALE": "it",
        }
    )

    with app.app_context():
        from gflask import models

        models.create_all()

    yield app

    with app.app_context():
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
