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
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from . import validate
from .models import User

bp = Blueprint("auth", __name__)


@bp.before_app_request
def require_verification():
    if not request.endpoint:
        return

    if current_user.is_authenticated:
        current_app.logger.info(f"endpoint: {request.endpoint}")
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
    login_user(user)
    # return redirect(url_for("main.index"))
    return redirect(url_for("auth.verify_email"))


@bp.route("/forgot")
def forgot():
    return "Forgot!"


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
    return redirect(url_for("auth.verify_email"))


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))


def _get_next():
    next_page = request.args.get("next")
    if not next_page or not next_page.startswith("/") or next_page.startswith("//"):
        next_page = url_for("main.index")
    return next_page
