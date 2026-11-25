from flask import Blueprint, abort, redirect, render_template, session

from app.database.db import get_session
from app.models import User
from app.services.teacher_analytics_service import all_student_performance, class_overview, student_analytics

bp = Blueprint("teacher", __name__, url_prefix="/teacher")


def _teacher_required():
    if "user_id" not in session:
        return redirect("/")
    if session.get("user_role") not in {"teacher", "admin"}:
        abort(403)
    return None


@bp.route("/")
def dashboard():
    access_denied = _teacher_required()
    if access_denied:
        return access_denied
    with get_session() as db_session:
        overview = class_overview(db_session)
        performance = all_student_performance(db_session)
    return render_template("teacher/dashboard.html", overview=overview, performance=performance)


@bp.route("/students/<int:student_id>")
def student_detail(student_id: int):
    access_denied = _teacher_required()
    if access_denied:
        return access_denied
    with get_session() as db_session:
        student = db_session.get(User, student_id)
        if student is None or student.role != "student":
            abort(404)
        report = student_analytics(db_session, student.id)
        student_data = {"code": student.student_code, "name": student.name}
    return render_template("teacher/student_detail.html", student=student_data, report=report)