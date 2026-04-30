from flask import Blueprint, render_template

from app.models import Lesson, LessonEvent, LessonParticipant
from app.routes.guards import roles_required

teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher")


@teacher_bp.get("/dashboard")
@roles_required("teacher", "admin")
def dashboard():
    lessons = Lesson.query.order_by(Lesson.starts_at.desc()).limit(20).all()
    return render_template("teacher/dashboard.html", lessons=lessons)


@teacher_bp.get("/lesson/<int:lesson_id>")
@roles_required("teacher", "admin")
def lesson_live(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    participants = LessonParticipant.query.filter_by(lesson_id=lesson.id).all()
    events = (
        LessonEvent.query.filter_by(lesson_id=lesson.id)
        .order_by(LessonEvent.created_at.desc())
        .limit(100)
        .all()
    )
    return render_template("teacher/lesson_live.html", lesson=lesson, participants=participants, events=events)

