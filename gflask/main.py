from flask import Blueprint
from flask import flash
from flask import render_template
from flask_login import current_user
from flask_login import login_required

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    # flash("Success", "success")
    # flash("Warning", "warning")
    # flash("Danger", "danger")
    return render_template("index.html")

