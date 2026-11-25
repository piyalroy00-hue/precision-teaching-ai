from flask import Blueprint, abort, redirect, render_template, request, session

from app.database.db import get_session
from app.services.admin_service import delete_user, list_users, reset_user_password

bp = Blueprint("admin", __name__, url_prefix="/admin")


def _admin_required():
    if "user_id" not in session:
        return redirect("/")
    if session.get("user_role") != "admin":
        abort(403)
    return None


@bp.route("/", methods=["GET", "POST"])
def dashboard():
    access_denied = _admin_required()
    if access_denied:
        return access_denied
    error = None
    success = None
    if request.method == "POST":
        action = request.form.get("action")
        user_id = request.form.get("user_id", type=int)
        try:
            if user_id is None:
                raise ValueError("A user must be selected.")
            with get_session() as db_session:
                if action == "delete":
                    delete_user(db_session, user_id, session["user_id"])
                    success = "User and associated learning records were removed."
                elif action == "reset_password":
                    reset_user_password(db_session, user_id, request.form.get("new_password", ""))
                    success = "Password reset successfully."
                else:
                    raise ValueError("Unsupported administrative action.")
        except ValueError as exc:
            error = str(exc)

    with get_session() as db_session:
        users = [
            {
                "id": user.id, "student_code": user.student_code, "name": user.name,
                "email": user.email, "role": user.role, "department": user.department,
                "semester": user.semester, "created_at": user.created_at.strftime("%Y-%m-%d"),
            }
            for user in list_users(db_session)
        ]
    return render_template("admin/dashboard.html", users=users, error=error, success=success)