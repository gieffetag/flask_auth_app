from gflask.models import User


def test_signup_page_loads(client):
    """Verifica che la pagina di registrazione risponda con 200 OK."""
    response = client.get("/signup")
    assert response.status_code == 200
    assert b"Registrati" in response.data or b"Sign up" in response.data


def test_successful_signup(client, app):
    """Verifica che la registrazione crei un utente nel database."""
    # Simuliamo l'invio del form di registrazione
    response = client.post(
        "/signup",
        data={
            "name": "Mario Rossi",
            "email": "mario@example.com",
            "password": "Password123!",  # Usa una password che passa il tuo validator
        },
        follow_redirects=True,
    )  # follow_redirects segue il redirect a /verify

    # Controlliamo che l'utente sia stato creato nel DB
    with app.app_context():
        user = User.select(email="mario@example.com")
        assert len(user) == 1
        assert user[0].name == "Mario Rossi"
        assert user[0].is_verified == 0
        assert user[0].verification_code != ""
