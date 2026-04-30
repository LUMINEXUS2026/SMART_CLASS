from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user

from app.models import Lesson, LessonParticipant
from app.routes.guards import roles_required

student_bp = Blueprint("student", __name__, url_prefix="/student")


@student_bp.get("/dashboard")
@roles_required("student")
def dashboard():
    active_lessons = Lesson.query.filter_by(status="active").order_by(Lesson.starts_at.desc()).all()
    my_participations = LessonParticipant.query.filter_by(student_id=current_user.id).all()
    joined_ids = {p.lesson_id for p in my_participations}
    return render_template("student/dashboard.html", active_lessons=active_lessons, joined_ids=joined_ids)


@student_bp.get("/lesson/<int:lesson_id>")
@roles_required("student")
def lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    if lesson.status != "active":
        return redirect(url_for("student.dashboard"))
    return render_template("student/lesson.html", lesson=lesson)

