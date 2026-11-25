from flask import Blueprint, redirect, render_template, request, session

from app.database.db import get_session
from app.services.auth_service import AuthError, authenticate, register_student

bp = Blueprint("auth", __name__)


def _landing_page_for_role(role: str) -> str:
    if role == "admin":
        return "/admin/"
    if role == "teacher":
        return "/teacher/"
    return "/dashboard"


@bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        try:
            with get_session() as db_session:
                user = authenticate(db_session, email, password)
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["user_student_code"] = user.student_code
            session["user_email"] = user.email
            session["user_role"] = user.role
            return redirect(_landing_page_for_role(user.role))
        except AuthError as exc:
            return render_template("auth/login.html", error=str(exc))

    if "user_id" in session:
        return redirect(_landing_page_for_role(session.get("user_role", "student")))
    return render_template("auth/login.html")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        student_code = request.form.get("student_code", "").strip()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        department = request.form.get("department", "Computer Science").strip()
        semester = request.form.get("semester", "1").strip()

        if not student_code or not name or not email or not password:
            return render_template("auth/register.html", error="Please fill in all fields.")

        try:
            with get_session() as db_session:
                register_student(
                    db_session,
                    student_code=student_code,
                    name=name,
                    email=email,
                    password=password,
                    department=department or None,
                    semester=int(semester) if semester.isdigit() else None,
                )
            return render_template("auth/register.html", success="Account created successfully.")
        except AuthError as exc:
            return render_template("auth/register.html", error=str(exc))

    return render_template("auth/register.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")
