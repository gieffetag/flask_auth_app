import os

import pytest
from gflask import create_app
from gflask.database import db


@pytest.fixture
def app():
    """Crea e configura una nuova istanza dell'app per ogni test."""
    # Impostiamo l'app in modalità testing e usiamo un DB in memoria
    os.environ["FLASK_TESTING"] = "true"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,  # Disabilita CSRF per semplificare i test dei form
            "BABEL_DEFAULT_LOCALE": "it",
        }
    )

    # Creiamo le tabelle nel DB in memoria prima del test
    with app.app_context():
        from gflask import models

        models.create_all()

    yield app

    # Eliminiamo tutto dopo il test per avere un ambiente pulito
    with app.app_context():
        models.drop_all()


@pytest.fixture
def client(app):
    """Un client di test per fare richieste (GET, POST) all'applicazione."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Un runner per testare i comandi CLI di Flask."""
    return app.test_cli_runner()
