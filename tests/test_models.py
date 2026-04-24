from werkzeug.security import generate_password_hash

from gflask.models import User


def test_user_create_and_get(app):
    """Verifica che un utente possa essere creato e recuperato."""
    with app.app_context():
        u = User(email="mario@example.com", name="Mario", password="hash")
        user_id = u.add()

        # Test Get
        db_user = User.get(user_id)
        assert db_user is not None
        assert db_user.email == "mario@example.com"

        # Test Select
        users = User.select(email="mario@example.com")
        assert len(users) == 1
        assert users[0].name == "Mario"


def test_user_verification_flow(app):
    """Verifica la generazione del codice e la verifica."""
    with app.app_context():
        u = User(email="luigi@example.com", password="hash")
        u.add()
        user = User.get(u.user_id)

        code = user.generate_verification_code()
        assert len(code) == 6
        assert user.is_verified == 0

        user.verified()
        assert user.is_verified == 1
        assert user.verification_code == ""


def test_user_updates(app, verified_user):
    """Verifica i vari metodi di update."""
    with app.app_context():
        user = User.get(verified_user.user_id)

        # Test Update Profile
        user.update_profile("Nuovo Nome", "en")
        updated = User.get(user.user_id)
        assert updated.name == "Nuovo Nome"
        assert updated.locale == "en"

        # Test Update Password (setta anche is_verified a 1 e svuota il code)
        user.update_password("new_hash")
        updated = User.get(user.user_id)
        assert updated.password == "new_hash"

        # Test Update Email (deve resettare la verifica)
        user.update_email("new_email@example.com")
        updated = User.get(user.user_id)
        assert updated.email == "new_email@example.com"
        assert updated.is_verified == 0


def test_delete_account(app, verified_user):
    """Verifica l'eliminazione dell'account."""
    with app.app_context():
        user = User.get(verified_user.user_id)
        user.delete_account()

        assert User.get(verified_user.user_id) is None
