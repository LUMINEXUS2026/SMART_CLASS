from collections import Counter

from flask import Blueprint, render_template

from app.extensions import db
from app.models import Lesson, LessonEvent
from app.routes.guards import roles_required
from app.services.event_service import create_event

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.get("/lesson/<int:lesson_id>")
@roles_required("teacher", "admin")
def lesson_report(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    events = LessonEvent.query.filter_by(lesson_id=lesson.id).order_by(LessonEvent.created_at.asc()).all()
    if not any(event.event_type == "lesson_summary_ready" for event in events):
        create_event(lesson.id, None, "lesson_summary_ready", "system", {})
        db.session.commit()
        events = LessonEvent.query.filter_by(lesson_id=lesson.id).order_by(LessonEvent.created_at.asc()).all()
    counts = Counter(event.event_type for event in events)
    return render_template("teacher/report.html", lesson=lesson, events=events, counts=counts)

