import hashlib

from flask import Blueprint
from flask import current_app
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from . import mail
from . import validate
from .models import User

bp = Blueprint("auth", __name__)


@bp.before_app_request
def require_verification():
    if not request.endpoint:
        return

    if current_user.is_authenticated:
        # current_app.logger.info(f"endpoint: {request.endpoint}")
        if not current_user.is_verified:
            # Note: you might need to prefix with blueprint name,
            # e.g., 'auth.verify_email'
            allowed_endpoints = [
                "auth.verify_email",
                "auth.verify_email_post",
                "auth.logout",
                "auth.resend_code",
                "static",
            ]
            if request.endpoint not in allowed_endpoints:
                flash("Please verify your email address to continue.", "warning")
                return redirect(url_for("auth.verify_email", next=request.full_path))


@bp.route("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    return render_template("login.html")


@bp.route("/login", methods=["POST"])
def login_post():
    email = request.form.get("email")
    password = request.form.get("password")
    remember = True if request.form.get("remember") else False
    next_page = _get_next()

    user = User.select(email=email)
    if user:
        user = user[0]

    if not user or not check_password_hash(user.password, password):
        flash("Please check your login details and try again.", "warning")
        return redirect(url_for("auth.login", next=next_page))

    login_user(user, remember=remember)
    return redirect(next_page)


@bp.route("/signup")
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    return render_template("signup.html")


@bp.route("/signup", methods=["POST"])
def signup_post():
    validator = validate.Validator(request.form)
    email = validator.check("email", "email")
    name = validator.check("name", "is_string")
    password = validator.check("password", "password")

    if validator.is_ok:
        user = User.select(email=email)
        if user:
            validator.errors["email"] = "Email address already exists"

    if not validator.is_ok:
        ctx = {
            "email": email,
            "name": name,
            "password": password,
            "errors": validator.errors,
        }
        return render_template("signup.html", **ctx)

    new_user = User(email=email, name=name, password=generate_password_hash(password))
    new_user.add()
    flash("User %s created successfully" % new_user.user_id, category="success")
    user = User.get(new_user.user_id)
    user.generate_verification_code()
    _send_verification_email(user)
    login_user(user)
    # return redirect(url_for("main.index"))
    return redirect(url_for("auth.verify_email"))


@bp.route("/verify")
@login_required
def verify_email():
    if current_user.is_verified:
        next_page = _get_next()
        return redirect(next_page)
    return render_template("verify.html")


@bp.route("/verify", methods=["POST"])
@login_required
def verify_email_post():
    next_page = _get_next()
    if current_user.is_verified:
        return redirect(next_page)
    code = request.form.get("code")
    if code == current_user.verification_code:
        current_user.verified()
        flash("Email successfully verified! Welcome!", "success")
        return redirect(next_page)
    else:
        flash("Invalid verification code. Please try again.", "danger")
        return redirect(url_for("auth.verify_email", next=next_page))


@bp.route("/resend_code")
@login_required
def resend_code():
    current_user.generate_verification_code()
    _send_verification_email(current_user)
    return redirect(url_for("auth.verify_email"))


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@bp.route("/forgot")
def forgot():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    return render_template("forgot.html")


@bp.route("/forgot", methods=["POST"])
def forgot_post():
    email = request.form.get("email")
    user = User.select(email=email)
    if user:
        # L'utente esiste, generiamo il token e inviamo la mail
        user = user[0]
        token = get_reset_token(user)
        _send_password_reset_email(user, token)

    flash(
        "Se l'indirizzo email è registrato, "
        "riceverai a breve un link per reimpostare la password.",
        "success",
    )
    return redirect(url_for("auth.login"))


@bp.route("/reset/<token>")
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    # Verifica la validità del token
    email = verify_reset_token(token)
    if not email:
        flash(
            "Il link di recupero è invalido o scaduto. Richiedine uno nuovo.", "danger"
        )
        return redirect(url_for("auth.forgot"))

    return render_template("reset.html", token=token)


@bp.route("/reset/<token>", methods=["POST"])
def reset_password_post(token):
    ## Verifica Token
    email = verify_reset_token(token)
    if not email:
        flash(
            "Il link di recupero è invalido o scaduto. Richiedine uno nuovo.", "danger"
        )
        return redirect(url_for("auth.forgot"))

    ## Valida la nuova password
    validator = validate.Validator(request.form)
    password = validator.check("password", "password")

    if not validator.is_ok:
        return render_template("reset.html", errors=validator.errors, token=token)

    ## Aggiorna la password
    user = User.select(email=email)[0]
    user.update_password(generate_password_hash(password))

    flash(
        "La tua password è stata aggiornata con successo! Ora puoi fare il login.",
        "success",
    )
    return redirect(url_for("auth.login"))


@bp.route("/settings")
@login_required
def settings():
    return render_template("settings.html")


@bp.route("/settings/name", methods=["POST"])
@login_required
def settings_name():
    name = request.form.get("name")
    errors = {}
    if not name or len(name) < 3:
        errors["name"] = "Il nome deve contenere almeno 3 caratteri."
        return render_template(
            "settings.html", open_modal="modal-name", name_input=name, errors=errors
        )

    current_user.update_name(name)
    flash("Nome aggiornato con successo.", "success")
    return redirect(url_for("auth.settings"))


@bp.route("/settings/password", methods=["POST"])
@login_required
def settings_password():
    current_pwd = request.form.get("current_password")
    new_pwd = request.form.get("new_password")
    errors = {}

    if not check_password_hash(current_user.password, current_pwd):
        errors["current_password"] = "La password attuale non è corretta."
        return render_template(
            "settings.html", open_modal="modal-password", errors=errors
        )

    validator = validate.Validator(request.form)
    validator.check("new_password", "password")

    if not validator.is_ok:
        return render_template(
            "settings.html", open_modal="modal-password", errors=validator.errors
        )

    current_user.update_password(generate_password_hash(new_pwd))
    flash("Password aggiornata con successo.", "success")
    return redirect(url_for("auth.settings"))


@bp.route("/settings/email", methods=["POST"])
@login_required
def settings_email():
    current_pwd = request.form.get("current_password")
    new_email = request.form.get("new_email")
    errors = {}

    if not check_password_hash(current_user.password, current_pwd):
        errors["current_password"] = "Password non corretta."
        return render_template(
            "settings.html",
            open_modal="modal-email",
            email_input=new_email,
            errors=errors,
        )

    if User.select(email=new_email):
        errors["new_email"] = "Email già in uso."
        return render_template(
            "settings.html",
            open_modal="modal-email",
            email_input=new_email,
            errors=errors,
        )

    current_user.update_email(new_email)
    current_user.generate_verification_code()
    _send_verification_email(current_user)
    flash("Email aggiornata. Controlla la posta per la verifica.", "success")
    return redirect(url_for("main.index"))


@bp.route("/settings/delete", methods=["POST"])
@login_required
def settings_delete():
    current_pwd = request.form.get("current_password")
    if not check_password_hash(current_user.password, current_pwd):
        flash("Password errata. Impossibile eliminare l'account.", "danger")
        return render_template("settings.html", open_modal="modal-delete")

    current_user.delete_account()
    logout_user()
    flash("Account eliminato definitivamente.", "success")
    return redirect(url_for("main.index"))


# ------------------------------------------------------------------ #


def _get_next():
    next_page = request.args.get("next")
    if not next_page or not next_page.startswith("/") or next_page.startswith("//"):
        next_page = url_for("main.index")
    return next_page


def _send_verification_email(user):
    content = (
        f"Ciao {user.name or 'Utente'},\n\n"
        f"Il tuo codice di verifica è: {user.verification_code}\n\n"
        "Inseriscilo nell'applicazione per continuare."
    )
    subject = f"[{current_app.config.get('APP_NAME', 'App')}] Codice di verifica"

    # Recupera un mittente predefinito da app.config, o usa un fallback
    sender_email = current_app.config.get("EMAIL", {}).get(
        "default_sender", "noreply@example.com"
    )

    mail_args = {
        "from": {
            "name": current_app.config.get("APP_NAME", "App"),
            "email": sender_email,
        },
        "to": [{"name": user.name or "Utente", "email": user.email}],
        "subject": subject,
        "content": content,
    }

    mail.send(mail_args)


def get_reset_token(user):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    pwd_sig = hashlib.sha256(user.password.encode()).hexdigest()[:16]

    # Firma il payload con l'hash della password attuale cosi' dopo
    # che la password e' stata modificata l'hash non e' piu' valido
    payload = {"email": user.email, "pwd_sig": pwd_sig}
    return s.dumps(payload, salt="password-reset-salt")


def verify_reset_token(token, max_age=3600):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        payload = s.loads(token, salt="password-reset-salt", max_age=max_age)
        email = payload.get("email")
        token_pwd_sig = payload.get("pwd_sig")
        user = User.select(email=email)
        if not user:
            return None
        user = user[0]
        current_pwd_sig = hashlib.sha256(user.password.encode()).hexdigest()[:16]

        # Se l'hash della password attuale e' diverso dall'hash estratto
        # dal token significa che il token e' gia' stato usato per
        # reimpostare la password
        if token_pwd_sig != current_pwd_sig:
            return None

        return email

    except Exception:
        return None


def _send_password_reset_email(user, token):
    reset_url = url_for("auth.reset_password", token=token, _external=True)
    content = (
        f"Ciao {user.name or 'Utente'},\n\n"
        f"Per reimpostare la tua password, clicca sul seguente link:\n"
        f"{reset_url}\n\n"
        "Se non hai richiesto tu il reset, ignora semplicemente questa email."
    )
    subject = f"[{current_app.config.get('APP_NAME', 'App')}] Recupero Password"
    sender_email = current_app.config.get("EMAIL", {}).get(
        "default_sender", "noreply@example.com"
    )

    mail_args = {
        "from": {
            "name": current_app.config.get("APP_NAME", "App"),
            "email": sender_email,
        },
        "to": [{"name": user.name or "Utente", "email": user.email}],
        "subject": subject,
        "content": content,
    }
    mail.send(mail_args)
