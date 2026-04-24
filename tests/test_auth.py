from flask import url_for
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from gflask.models import User


def test_signup(client, app):
    """Verifica che la registrazione crei un utente non verificato."""
    response = client.post(
        "/signup",
        data={
            "name": "Mario Rossi",
            "email": "mario@example.com",
            "password": "Password123!",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    with app.app_context():
        users = User.select(email="mario@example.com")
        assert len(users) == 1
        assert users[0].is_verified == 0


def test_login_success(client, verified_user):
    """Verifica un login corretto."""
    response = client.post(
        "/login",
        data={"email": "test@example.com", "password": "Password123!"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    # Verifica che appaia il nome utente del menu dropdown post-login
    assert b"Test User" in response.data


def test_login_failure(client, verified_user):
    """Verifica che una password errata blocchi il login."""
    response = client.post(
        "/login",
        data={"email": "test@example.com", "password": "Sbagliata!"},
        follow_redirects=True,
    )
    # Se il login fallisce, la barra di navigazione deve avere il tasto "Login"
    assert b"Login" in response.data
    assert b"Test User" not in response.data


def test_verification_required_middleware(client, app):
    """Verifica che un utente NON verificato sia bloccato dal middleware."""
    with app.app_context():
        # Usa una password hashata corretta per permettere il login!
        u = User(
            email="unverified@test.com", password=generate_password_hash("Password123!")
        )
        u.add()

    # Eseguiamo il login corretto (ci farà entrare, ma saremo unverified)
    client.post(
        "/login", data={"email": "unverified@test.com", "password": "Password123!"}
    )

    # Proviamo ad accedere a una rotta protetta come il settings o profile
    response = client.get("/profile", follow_redirects=True)

    # Il middleware ci deve aver reindirizzato a /verify!
    assert (
        b"verifica il tuo indirizzo" in response.data.lower()
        or b"verify" in response.data.lower()
    )


def test_forgot_password_and_reset(client, app, verified_user):
    """Verifica il flusso di recupero password."""
    response = client.post(
        "/forgot", data={"email": "test@example.com"}, follow_redirects=True
    )
    assert response.status_code == 200

    with app.app_context():
        from gflask.auth import get_reset_token

        user = User.get(verified_user.user_id)
        token = get_reset_token(user)

    response = client.post(
        f"/reset/{token}", data={"password": "NewPassword123!"}, follow_redirects=True
    )

    with app.app_context():
        user = User.get(verified_user.user_id)
        assert check_password_hash(user.password, "NewPassword123!")


def test_settings_update_profile(client, verified_user, app):
    """Verifica la modifica del nome e della lingua."""
    client.post(
        "/login", data={"email": "test@example.com", "password": "Password123!"}
    )

    response = client.post(
        "/settings/name",
        data={"name": "Nuovo Nome Test", "locale": "en"},
        follow_redirects=True,
    )

    with app.app_context():
        user = User.get(verified_user.user_id)
        assert user.name == "Nuovo Nome Test"
        assert user.locale == "en"


def test_settings_delete_account(client, verified_user, app):
    """Verifica che la cancellazione rimuova l'utente ed esegua il logout."""
    client.post(
        "/login", data={"email": "test@example.com", "password": "Password123!"}
    )

    response = client.post(
        "/settings/delete",
        data={"current_password": "Password123!"},
        follow_redirects=True,
    )

    with app.app_context():
        user = User.get(verified_user.user_id)
        assert user is None
